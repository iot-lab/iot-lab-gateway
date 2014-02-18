#include <stdint.h>
#include <stdio.h>

#include "measures_handler.h"
#include "command_reader.h"
#include "constants.h"
#include "decode.h"
#include "common.h"


void decode_pkt(struct pkt *current_pkt)
{
        uint8_t pkt_type = current_pkt->data[0];
        int ret;

        DEBUG_PRINT_PACKET(current_pkt->data, current_pkt->len);

        if ((pkt_type & ASYNC_FRAME_MASK) == ASYNC_FRAME_MASK) {
                // send to measures packets handler
                ret = handle_measure_pkt(current_pkt->data, current_pkt->len);
        } else {
                // answer commands
                ret = write_answer(current_pkt->data, current_pkt->len);
        }

        if (ret) {
                PRINT_ERROR("Error in decode packet: ret %d: " \
                                "len %d - 0x%02X 0x%02X\n", ret,
                                current_pkt->len,
                                current_pkt->data[0],
                                current_pkt->data[1]);
        }


}

