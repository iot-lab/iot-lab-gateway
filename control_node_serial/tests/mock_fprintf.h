/*
 * Mock log_print
 */

char print_buff[2048];
#define fprintf(stream, ...)  snprintf(print_buff, sizeof(print_buff), __VA_ARGS__)

