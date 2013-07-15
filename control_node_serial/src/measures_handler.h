#ifndef MEASURES_HANDLER_H
#define MEASURES_HANDLER_H

#include <stddef.h>

extern void init_measures_handler(void);
extern int handle_measure_pkt(unsigned char *data, size_t len);


#endif // MEASURES_HANDLER_H
