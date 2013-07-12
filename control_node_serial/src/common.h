#ifndef COMMON_H
#define COMMON_H

#ifndef DEBUG
#define DEBUG 0
#endif // DEBUG

#define MSG_OUT   (stderr)
#define LOG       (stdout)

#define PRINT_MSG(args ...)   fprintf(MSG_OUT, args)
#define PRINT_ERROR(args ...)  do {\
        PRINT_MSG("cn_serial_error :"); \
        PRINT_MSG(args);\
} while (0)


#if DEBUG
#include <stdio.h>
#define DEBUG_PRINT(args ...) fprintf(LOG, args)
#else
#define DEBUG_PRINT(args ...)
#endif


#if DEBUG
#define DEBUG_PRINT_PACKET(len, data)  do{ \
                for (char i=0; i < ((char) (len)); i++) {\
                        DEBUG_PRINT(" %02X", (data)[i]);\
                }\
                DEBUG_PRINT("\n");\
        }while(0)
#else
#define DEBUG_PRINT_PACKET(len, data)
#endif

#if 0
void debug_print_packet(unsigned int len, unsigned char *data) {
        for (uint8_t i=0; i < current_pkt->len; i++) {
                DEBUG_PRINT(" %02X", current_pkt->data[i]);
        }
        DEBUG_PRINT("\n");
}
#endif

#endif // COMMON_H
