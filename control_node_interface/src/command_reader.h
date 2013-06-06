#ifndef COMMAND_READER_H
#define COMMAND_READER_H

#include <stdint.h>

extern int command_reader_start(int serial_fd);
extern int write_answer(char *data, size_t len);


#endif // COMMAND_READER_H
