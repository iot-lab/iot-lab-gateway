#ifndef SNIFFER_ZEP_F
#define SNIFFER_ZEP_F
#endif // SNIFFER_ZEP_F

#include <stdint.h>

void sniffer_zep_send(uint32_t timestamp_s, uint32_t timestamp_us,
                      uint8_t channel, int8_t rssi, uint8_t lqi,
                      uint8_t crc_ok, uint8_t length, uint8_t *payload);
