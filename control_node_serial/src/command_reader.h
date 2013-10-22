#ifndef COMMAND_READER_H
#define COMMAND_READER_H

#include <stddef.h>

extern int command_reader_start(int serial_fd);
extern int write_answer(unsigned char *data, size_t len);


#endif // COMMAND_READER_H
