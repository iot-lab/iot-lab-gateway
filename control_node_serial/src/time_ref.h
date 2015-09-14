/*******************************************************************************
# This file is a part of IoT-LAB gateway_code
# Copyright (C) 2015 INRIA (Contact: admin@iot-lab.info)
# Contributor(s) : see AUTHORS file
#
# This software is governed by the CeCILL license under French law
# and abiding by the rules of distribution of free software.  You can  use,
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# http://www.cecill.info.
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.
*******************************************************************************/

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
