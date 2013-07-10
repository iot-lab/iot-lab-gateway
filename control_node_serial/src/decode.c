#include <stdint.h>

#include "measures_handler.h"
#include "command_reader.h"
#include "constants.h"
#include "decode.h"


void decode_pkt(struct pkt *current_pkt)
{
        uint8_t pkt_type = current_pkt->data[0];

#if DEBUG
        for (uint8_t i=0; i < current_pkt->len; i++) {
                DEBUG_PRINT(" %02X", current_pkt->data[i]);
        }
        DEBUG_PRINT("\n");
#endif

        if ((pkt_type & MEASURES_FRAME_MASK) == MEASURES_FRAME_MASK) {
                // send to measures packets handler
                handle_measure_pkt(current_pkt->data, current_pkt->len);
        } else {
                // answer commands
                write_answer(current_pkt->data, current_pkt->len);
        }
}

