#ifndef COMMON_H
#define COMMON_H

#ifndef DEBUG
#define DEBUG 0
#endif // DEBUG

#define MSG_OUT   (stderr)
#define LOG       (stdout)

#define PRINT_MSG(args ...)   fprintf(MSG_OUT, args)
#define PRINT_ERROR(fmt, ...)  do {\
        PRINT_MSG("cn_serial_error : " fmt, __VA_ARGS__);\
} while (0)


#if DEBUG
#include <stdio.h>
#define DEBUG_PRINT(args ...) fprintf(LOG, args)
#else
#define DEBUG_PRINT(args ...)
#endif


#if DEBUG
#define DEBUG_PRINT_PACKET(data, len)  do{ \
                for (unsigned char i=0; i < (len); i++) {\
                        DEBUG_PRINT(" %02X", (data)[i]);\
                }\
                DEBUG_PRINT("\n");\
        }while(0)
#else
#define DEBUG_PRINT_PACKET(len, data)
#endif

#endif // COMMON_H
