#ifndef COMMON_H
#define COMMON_H

#ifndef DEBUG
#define DEBUG 0
#endif // DEBUG

#define MSG_OUT   (stderr)
#define LOG       (stdout)

#if DEBUG
#include <stdio.h>
#define DEBUG_PRINT(args ...) fprintf(LOG, args)
#else
#define DEBUG_PRINT(args ...)
#endif

#endif // COMMON_H
