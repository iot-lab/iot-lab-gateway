/*******************************************************************************
# This file is a part of IoT-LAB gateway_code
# Copyright (C) 2015 INRIA (Contact: admin@iot-lab.info)
# Contributor(s) : see AUTHORS file
#
# This software is governed by the CeCILL license under French law
# and abiding by the rules of distribution of free software.  You can  use,
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# http://www.cecill.info.
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.
*******************************************************************************/

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
} sniffer_state = {0, 0, -1, 0, -1};

static void *sniffer_thread(void *attr);
static int create_server_socket(void);


int sniffer_server_start()
{
    int socket_fd = create_server_socket();
    if (-1 == socket_fd)
        return 1;
    sniffer_state.socket_fd = socket_fd;
    sniffer_state.running = 1;
    sniffer_state.active_connection = 0;
    sniffer_state.connect_fd = -1;  // default to an invalid filedescriptor
    return pthread_create(&sniffer_state.thread, NULL, sniffer_thread, NULL);
}


void sniffer_server_stop()
{
    pthread_kill(sniffer_state.thread, SIGPIPE);
    sniffer_state.running = 0;
    close(sniffer_state.connect_fd);
    close(sniffer_state.socket_fd);
    sniffer_state.connect_fd = -1;  // default to an invalid filenumber
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
    close(s_fd);
    return -1;
}


/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * We want 'active_connection' to be always at 1 when there is a client.
 * It can be put back to 0 if a 'send' fails.
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *
 * The tricky part is when the sending fails exactly at the same moment where a
 * new connection happens.
 *
 * There might be 'active_connection' with no 'real' client, it's not a problem
 * as it will be updated on the next send.
 *
 */

/* http://en.wikipedia.org/wiki/Berkeley_sockets */
static void *sniffer_thread(void *attr)
{
    (void)attr;
    int connect_fd = -1;
    while (sniffer_state.running) {
        connect_fd = accept(sniffer_state.socket_fd, NULL, NULL);
        if (0 > connect_fd) {
            PRINT_ERROR("error accept failed\n");
            sleep(1);
            continue;
        }

        // Keep only one connection active
        if (0 > sniffer_state.connect_fd) {
            shutdown(sniffer_state.connect_fd, SHUT_RDWR);
            close(sniffer_state.connect_fd);
        }

        // Keep the order synced with send_packet
        // set active_connection AFTER saving connect_fd
        sniffer_state.connect_fd = connect_fd;
        sniffer_state.active_connection = 1;
    }
    return NULL;
}


/* The following implementation may looks strange. It's 'only' a lock-less
 * method to ensure the validity of 'active_connection.
 *
 * Read the following if you want to understand.
 *
 * In normal case we want:
 *   Put 0 if the send fails
 *   Let 1 if the send succeeds
 *
 * But, to ensure consistency when a new connection happpens during send,
 * I put it a 0 at first, we send the message and put back to 1 if it succeeds.
 *
 * So even if a connection arrives and I'm using the OLD descriptor when
 * sending, I won't force a 0 with an active connection in background.
 *
 *
 * Other solutions might have been working, but my brain came only with this for
 * the moment.
 *
 */

size_t sniffer_server_send_packet(const uint8_t *data, size_t len)
{
    int ret;
    int connect_fd = -1;

    if (!sniffer_state.active_connection)
        return 0;

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
