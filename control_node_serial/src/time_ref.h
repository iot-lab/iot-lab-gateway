#ifndef TIME_REF_H
#define TIME_REF_H

#include <sys/time.h>
extern struct timeval set_time_ref;


/* Subtract the `struct timeval' values X and Y,
 *     storing the result in RESULT.
 *     Return 1 if the difference is negative, otherwise 0.
 */
int timeval_substract(struct timeval *result, struct timeval *x,
        struct timeval *y);

#endif // TIME_REF_H
