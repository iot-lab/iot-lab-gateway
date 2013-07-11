#include <stdint.h>

#include "measures_handler.h"
#include "command_reader.h"
#include "constants.h"
#include "decode.h"
#include "common.h"


void decode_pkt(struct pkt *current_pkt)
{
        uint8_t pkt_type = current_pkt->data[0];

        DEBUG_PRINT_PACKET(current_pkt->len, current_pkt->data);

        if ((pkt_type & MEASURES_FRAME_MASK) == MEASURES_FRAME_MASK) {
                // send to measures packets handler
                handle_measure_pkt(current_pkt->data, current_pkt->len);
        } else {
                // answer commands
                write_answer(current_pkt->data, current_pkt->len);
        }
}

