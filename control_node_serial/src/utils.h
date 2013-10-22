#ifndef UTILS_H
#define UTILS_H


#include <stdint.h>

/*
 * Dictionnaries implementation
 *     str -> uint8_t
 *
 *     * Values and keys should be unique.
 *     * Dict should be NULL terminated
 *

struct dict_entry example_d[] = {
        {"key1", val1},
        {"key2", val2},
        {"key3", val3},
        {NULL, 0},
};

 *
 */



struct dict_entry {
        char *str;
        unsigned char val;
};

int get_val(char *key, struct dict_entry dict[], uint8_t *val);
int get_key(uint8_t val, struct dict_entry dict[], char **key);


#endif // UTILS_H
