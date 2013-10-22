#ifndef MEASURES_HANDLER_H
#define MEASURES_HANDLER_H

#include <stddef.h>

void measures_handler_start(int print_measures, char *oml_config_file_path);
int handle_measure_pkt(unsigned char *data, size_t len);
void measures_handler_stop(void);


#endif // MEASURES_HANDLER_H
