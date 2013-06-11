#ifndef COMMON_H
#define COMMON_H

#define DEBUG 0

#define MSG_OUT   (stderr)
#define LOG       (stdout)

#if DEBUG
#include <stdio.h>
#define DEBUG_PRINT(args ...) fprintf(LOG, args)
#else
#define DEBUG_PRINT(args ...)
#endif

#endif // COMMON_H
