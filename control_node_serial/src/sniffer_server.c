#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif // _GNU_SOURCE
#include <unistd.h>
#include <signal.h>
#include <sys/socket.h>
#include <string.h>
#include <arpa/inet.h>
#include <pthread.h>

#include "sniffer_server.h"
#include "common.h"


#define SNIFFER_PORT 30000


static struct {
    pthread_t thread;
    volatile int running;
    volatile int socket_fd;
    volatile int active_connection;
    volatile int connect_fd;
} sniffer_state = {0, 0, 0, 0, 0};

static void *sniffer_thread(void *attr);
static int create_server_socket(void);


int sniffer_server_start()
{
    int socket_fd = create_server_socket();
    if (-1 == socket_fd)
        return 1;
    sniffer_state.socket_fd = socket_fd;
    sniffer_state.running = 1;
    return pthread_create(&sniffer_state.thread, NULL, sniffer_thread, NULL);
}


void sniffer_server_stop()
{
    pthread_kill(sniffer_state.thread, SIGPIPE);
    sniffer_state.running = 0;
    close(sniffer_state.connect_fd);
    close(sniffer_state.socket_fd);
}


int sniffer_server_has_active_connection()
{
    return sniffer_state.active_connection;
}


static int create_server_socket()
{
    struct sockaddr_in s_addr;
    memset(&s_addr, 0, sizeof(s_addr));

    int s_fd = socket(PF_INET, SOCK_STREAM, IPPROTO_TCP);
    int on = 1;

    if (-1 == s_fd) {
        PRINT_ERROR("cannot create socket\n");
        goto cleanup;
    }

    if (-1 == setsockopt(s_fd, SOL_SOCKET, SO_REUSEADDR, (char *)&on,
                sizeof(on))) {
        PRINT_ERROR("setsockopt failed");
        goto cleanup;
    }

    s_addr.sin_family      = AF_INET;
    s_addr.sin_port        = htons(SNIFFER_PORT);
    s_addr.sin_addr.s_addr = htonl(INADDR_ANY);

    if (-1 == bind(s_fd, (struct sockaddr *)&s_addr, sizeof(s_addr))) {
        PRINT_ERROR("error bind failed\n");
        goto cleanup;
    }

    if (-1 == listen(s_fd, 0)) {
        PRINT_ERROR("error listen failed\n");
        goto cleanup;
    }
    return s_fd;

cleanup:
    if (s_fd != -1)
        close(s_fd);
    return -1;
}


/* http://en.wikipedia.org/wiki/Berkeley_sockets */
static void *sniffer_thread(void *attr)
{
    (void)attr;
    while (sniffer_state.running) {
        /* Only one connection is kept at a time.
         * If there is a new connection, the previous one is closed.
         */
        int connect_fd = accept(sniffer_state.socket_fd, NULL, NULL);

        if (0 > connect_fd) {
            PRINT_ERROR("error accept failed\n");
            sleep(1);
            continue;
        }
        /* close previous connection at first, losing some packets on
         * disconnection is OK */
        shutdown(sniffer_state.connect_fd, SHUT_RDWR);
        close(sniffer_state.connect_fd);

        /* * * * Update connection
         * 'active_connection' should be true if there might be an active
         * connection running.
         * And it is better if it can be 0 when no connection is active
         *
         * It should NEVER be false with an active connection
         * (when outside of 'send_packet' function)
         * It should ALWAYS be true with an active connection
         * (when outside of 'send_packet' function)
         *
         */
        // Keep the order synced with send_packet to ensure active_connection
        // is never false with active connection
        sniffer_state.connect_fd = connect_fd;
        sniffer_state.active_connection = 1;
    }
    return NULL;
}

int sniffer_server_send_packet(const void *data, size_t len)
{
    int ret;
    int connect_fd;

    /* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
     * Goal: never ever have 'active_connection' 0 with an active connection
     * But try to put it to 0 when we detect that a connection is destroyed
     * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
     *
     * In normal case:
     *   Put 'active_connection' to 0. Send message, put it back to 1.
     *
     * When connection is closed:
     *   Put 'active_connection' to 0. Fail to send message, let it at 0.
     *
     *
     * If this happens when a new connection is being created:
     *   We put 0 in 'active connection'. Then we save 'connect_fd':
     *
     * Two cases:
     *   * We saved the old connect_fd: we are before the server thread updated
     *   connect_fd, and we won't touch 'active_connection' anymore,
     *   so the server will put it back to 1 as the line is after the connect_fd
     *   affectation => OK
     *
     *
     *   * We saved the new connect_fd, so the old one has been destroyed,
     *   the worst case, it that we wail to send the message on the new
     *   connection, the server thread already put 1 in active_connection,
     *   and we don't put it back to 0.
     *      We end up with 'active_connection' && 'no valid connection'
     *      But that's OK, it will be corrected on next message sent
     *
     */

    // Keep the 'active_connection' and 'connect_fd' affectations synced with
    // server thread
    sniffer_state.active_connection = 0;
    connect_fd = sniffer_state.connect_fd;

    ret = send(connect_fd, data, len, MSG_NOSIGNAL);
    if (ret == -1)
        close(connect_fd);  // Connection closed on client side, cleanup
    else
        sniffer_state.active_connection = 1;  // Connection is still active
    return ret;
}

