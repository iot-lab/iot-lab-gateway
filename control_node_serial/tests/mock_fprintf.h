#ifndef MOCK_FPRINTH_H
#define MOCK_FPRINTH_H

#ifdef fprintf
#undef fprintf
#endif //fprintf

char print_buff[2048];
#define fprintf(stream, ...)  snprintf(print_buff, sizeof(print_buff), __VA_ARGS__)


#endif // MOCK_FPRINTH_H
