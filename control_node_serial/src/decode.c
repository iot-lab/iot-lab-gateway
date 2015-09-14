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

