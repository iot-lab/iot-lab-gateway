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

#include <stdio.h>
#include <string.h>

#include <termios.h>
#include <unistd.h> // tcgetattr
#include <fcntl.h>  // open

#include <errno.h>
#include <sys/param.h> // MIN

#include <time.h>

#include "common.h"
#include "constants.h"



#include "serial.h"

static void parse_rx_data(unsigned char *rx_buff, unsigned int len,
                void (*handle_pkt)(struct pkt*));
static const unsigned char sync_byte = (unsigned char) SYNC_BYTE;


int configure_tty(char *tty_path)
{
        /*
         * TTY configuration inspired by:
         *   - Contiki/tunslip code
         *   - http://www.unixwiz.net/techtips/termios-vmin-vtime.html
         *   - termios manpage
         *   - http://www.tldp.org/HOWTO/Serial-Programming-HOWTO/x115.html
         */
        int serial_fd;
        struct termios tty;
        memset(&tty, 0, sizeof(tty));

        serial_fd = open(tty_path, O_RDWR | O_NOCTTY | O_SYNC);
        if (serial_fd == -1) {
                PRINT_ERROR("Could not open %s\n", tty_path);
                return -1;
        }
        if (tcflush(serial_fd, TCIOFLUSH) == -1) {
                PRINT_ERROR("Error in tcflush: %s\n",
                                strerror(errno));
                return -2;
        }
        if (tcgetattr(serial_fd, &tty)) {
                PRINT_ERROR("Error in tcgetattr: %s\n",
                                strerror(errno));
                return -3;
        }

        /*
         * Configure TTY
         */
        cfmakeraw(&tty);
        // blocking mode, should read at least 1 char and then can return
        tty.c_cc[VMIN]  = 1;
        tty.c_cc[VTIME] = 0;
        // Disable control characters and signals and all
        tty.c_cflag &= ~CRTSCTS; // Disable RTS/CTS (hardware) flow control
        tty.c_cflag &= ~HUPCL;   // No "hanging up" when closing
        tty.c_cflag |=  CLOCAL;  // ignore modem status line
        if (cfsetspeed(&tty, B500000)) {
                PRINT_ERROR("Error while setting terminal speed: %s\n",
                                strerror(errno));
                return -4;
        }

        // Apply and discard characters that may have arrived
        if (tcsetattr(serial_fd, TCSAFLUSH, &tty) == -1) {
                PRINT_ERROR("Error could not set attribute to tty: %s\n",
                                strerror(errno));
                return -5;
        }
        return serial_fd;
}


int receive_data(int fd, unsigned char *rx_buff, size_t len,
                void (*handle_pkt)(struct pkt*))
{
        int n_chars = 0;
        n_chars = read(fd, rx_buff, len);

        DEBUG_PRINT("n_chars %d\n", n_chars);
        if (n_chars > 0) {
                DEBUG_PRINT_PACKET(rx_buff, n_chars);
                parse_rx_data(rx_buff, n_chars, handle_pkt);
        } else if (n_chars == -1) {
                PRINT_ERROR("Error serial read: %s\n", strerror(errno));
        }
        return n_chars;

}


enum state_t {
        STATE_IDLE = 0,
        STATE_WAIT_LEN = 1,
        STATE_GET_PAYLOAD = 2,
};
static enum state_t state = STATE_IDLE;
static void parse_rx_data(unsigned char *rx_buff, unsigned len,
                void (*handle_pkt)(struct pkt*))
{
        // Current packet state
        static struct {
                struct pkt p;
                unsigned int cur_idx;
        } pkt;
        // Current parser state
        unsigned int cur_idx      = 0;
        // tmp variables
        unsigned char *sync_byte_addr;
        unsigned int n_bytes;

        while (len > cur_idx) {
                switch (state) {
                        case STATE_IDLE:
                                /*
                                 * Search for 'SYNC_BYTE' byte
                                 */
                                sync_byte_addr = (unsigned char *) memchr(
                                                &rx_buff[cur_idx], sync_byte,
                                                (len - cur_idx));
                                if (sync_byte_addr == NULL)
                                        return; // SYNC not found: drop data

                                cur_idx = (sync_byte_addr - rx_buff);
                                cur_idx++; // consume 'SYNC' byte
                                state   = STATE_WAIT_LEN;
                                break;
                        case STATE_WAIT_LEN:
                                /*
                                 * Read 'length' byte and initialize packet
                                 */
                                pkt.p.len   = rx_buff[cur_idx];
                                pkt.cur_idx = 0;

                                cur_idx++; // process 'len' byte
                                state = STATE_GET_PAYLOAD;
                                break;
                        case STATE_GET_PAYLOAD:
                                /*
                                 * Get missing bytes in payload,
                                 * or as much as available
                                 */
                                n_bytes = MIN((pkt.p.len - pkt.cur_idx),
                                                (len - cur_idx));
                                // copy data in 'pkt'
                                memcpy(&pkt.p.data[pkt.cur_idx],
                                                &rx_buff[cur_idx], n_bytes);
                                pkt.cur_idx += n_bytes;
                                cur_idx     += n_bytes;

                                // Packet full
                                if (pkt.p.len == pkt.cur_idx) {
                                        /* Handle packet and get back to idle */
                                        DEBUG_PRINT("Got pkt: %d\n", pkt.p.len);
                                        handle_pkt(&pkt.p);
                                        state = STATE_IDLE;
                                }
                                break;
                        default:
                                // Get out of here
                                state = STATE_IDLE;
                                break;
                }
        }
}
