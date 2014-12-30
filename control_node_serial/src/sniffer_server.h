#ifndef SNIFFER_SERVER_H
#define SNIFFER_SERVER_H

#include <stdint.h>
#include <stddef.h>

int sniffer_server_start(void);
void sniffer_server_stop(void);
size_t sniffer_server_send_packet(const uint8_t *data, size_t len);

#endif // SNIFFER_SERVER_H
