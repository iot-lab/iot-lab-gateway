#ifndef SNIFFER_HANDLER_H
#define SNIFFER_HANDLER_H

int start_sniffer_server(void);

void measure_sniffer_packet(uint32_t timestamp_s, uint32_t timestamp_us,
                            uint8_t channel, int8_t rssi, uint8_t lqi,
                            uint8_t crc_ok, uint8_t length, uint8_t *payload);
void stop_sniffer_server(void);

#endif // SNIFFER_HANDLER_H
