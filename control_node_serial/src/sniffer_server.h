#ifndef SNIFFER_SERVER_H
#define SNIFFER_SERVER_H

#include <stddef.h>

int sniffer_server_start(void);
void sniffer_server_stop(void);
int sniffer_server_send_packet(const void *data, size_t len);

#endif // SNIFFER_SERVER_H
