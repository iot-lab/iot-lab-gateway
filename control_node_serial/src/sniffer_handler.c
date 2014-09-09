#define _GNU_SOURCE
#include <unistd.h>
#include <string.h>
#include <signal.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <pthread.h>
#include "common.h"
#include "sniffer_handler.h"

#define SNIFFER_PORT 30000


static struct state {
    volatile int running;
    volatile int socket_fd;
    volatile int connect_fd;
    pthread_t thread;
} sniffer_state = {0, 0, 0, 0};
static void *sniffer_thread(void *attr);

static int create_server_socket()
{
    struct sockaddr_in s_addr;
    memset(&s_addr, 0, sizeof(s_addr));

    int s_fd = socket(PF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (-1 == s_fd) {
        PRINT_ERROR("cannot create socket\n");
        return -1;
    }

    s_addr.sin_family      = AF_INET;
    s_addr.sin_port        = htons(SNIFFER_PORT);
    s_addr.sin_addr.s_addr = htonl(INADDR_ANY);

    if (-1 == bind(s_fd, (struct sockaddr *)&s_addr, sizeof(s_addr))) {
        PRINT_ERROR("error bind failed\n");
        return -1;
    }

    if (-1 == listen(s_fd, 0)) {
        PRINT_ERROR("error listen failed\n");
        close(s_fd);
        return -1;
    }
    return s_fd;
}

int start_sniffer_server()
{
    int socket_fd = create_server_socket();
    if (-1 == socket_fd)
        return 1;
    sniffer_state.socket_fd = socket_fd;
    sniffer_state.running = 1;
    return pthread_create(&sniffer_state.thread, NULL, sniffer_thread, NULL);
}

void stop_sniffer_server()
{
    pthread_kill(sniffer_state.thread, SIGPIPE);
    sniffer_state.running = 0;
    close(sniffer_state.connect_fd);
    close(sniffer_state.socket_fd);
}

/* http://en.wikipedia.org/wiki/Berkeley_sockets */
static void *sniffer_thread(void *attr)
{
    (void)attr;
    sigset_t sigs_set;
    sigemptyset(&sigs_set);
    sigaddset(&sigs_set, SIGPIPE);

    struct sigaction act = {.sa_handler = SIG_IGN};
    sigaction(SIGPIPE, &act, NULL);

    while (sniffer_state.running) {
        int connect_fd = accept4(sniffer_state.socket_fd, NULL, NULL,
                SOCK_CLOEXEC);

        if (0 > connect_fd) {
            PRINT_ERROR("error accept failed");
            sleep(1);
            continue;
        }
        sniffer_state.connect_fd = connect_fd;
        // Wait SIGPIPE: client close connection or 'stop_sniffer_server'
        sigsuspend(&sigs_set);
        sniffer_state.connect_fd = 0;

        shutdown(connect_fd, SHUT_RDWR);
        close(connect_fd);
    }


    return NULL;
}



#define ZEP_V2_HEADER_LEN   32
#define ZEP_V2_ACK_LEN      8

#define ZEP_V2_TYPE_DATA    1
#define ZEP_V2_TYPE_ACK     2

#define ZEP_V2_MODE_LQI     0
#define ZEP_V2_MODE_CRC     1

static const struct {
    const uint8_t preamble_1;
    const uint8_t preamble_2;
    const uint8_t zep_version;
    const uint8_t packet_type;
} zep_header = {'E', 'X', '2', ZEP_V2_TYPE_DATA};
static const uint8_t lqi_crc_mode = ZEP_V2_MODE_LQI;
static const uint16_t ne_mote_id = 0;  // TODO

static void append_data(uint8_t **dst, const uint8_t *src, size_t len);

/*
 * ZEP v2 Header will have the following format (if type=1/Data):
 * |Preamble|Version| Type /
 * |2 bytes |1 byte |1 byte/
 * /Channel ID|Device ID|CRC/LQI Mode|LQI Val/
 * /  1 byte  | 2 bytes |   1 byte   |1 byte /
 * /NTP Timestamp|Sequence#|Reserved|Length|
 * /   8 bytes   | 4 bytes |10 bytes|1 byte|
 */
void measure_sniffer_packet(uint32_t timestamp_s, uint32_t timestamp_us,
                            uint8_t channel, int8_t rssi, uint8_t lqi,
                            uint8_t crc_ok, uint8_t length, uint8_t *payload)
{
    (void)rssi; (void)crc_ok;

    static uint32_t seqno = 0;
    uint32_t ne_seqno = htonl(++seqno);
    uint32_t ne_t_s = htonl(timestamp_s);
    uint32_t ne_t_us = htonl(timestamp_us);

    uint8_t zep_packet[256] = {0};
    uint8_t *pkt = zep_packet;


    append_data(&pkt, (uint8_t *)&zep_header, sizeof(zep_header));
    append_data(&pkt, &channel, sizeof(uint8_t));
    append_data(&pkt, (uint8_t *)&ne_mote_id, sizeof(uint16_t));
    append_data(&pkt, &lqi_crc_mode, sizeof(uint8_t));
    append_data(&pkt, &lqi, sizeof(uint8_t));

    append_data(&pkt, (uint8_t *)&ne_t_s, sizeof(uint32_t));
    append_data(&pkt, (uint8_t *)&ne_t_us, sizeof(uint32_t));

    append_data(&pkt, (uint8_t *)&ne_seqno, sizeof(uint32_t));

    pkt += 10;  // Reserved space 10

    // Cedric added two bytes after the packet:
    // https://github.com/adjih/exp-iotlab/blob/master/tools/SnifferHelper.py
    // I think for a CRC so I'm doing the same
    length += 2;  // add space for a crc (fake crc in fact)
    append_data(&pkt, &length, sizeof(uint8_t));
    append_data(&pkt, payload, length - 2);
    uint8_t crc[2] = {0xFF};
    append_data(&pkt, crc, 2);


    // DO something with zep_packet
    (void)zep_packet;

}

static void append_data(uint8_t **dst, const uint8_t *src, size_t len)
{
    memcpy(*dst, src, len);
    *dst += len;
}
