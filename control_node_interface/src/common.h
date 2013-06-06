#define DEBUG 1

#if DEBUG
#include <stdio.h>
#define DEBUG_PRINT(args ...) fprintf(stderr, args)
#else
#define DEBUG_PRINT(args ...)
#endif
