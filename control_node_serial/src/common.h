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

#ifndef COMMON_H
#define COMMON_H

#include <stdio.h>

#ifndef DEBUG
#define DEBUG 0
#endif // DEBUG

#define MSG_OUT   (stderr)
#define LOG       (stdout)

#define PRINT_MSG(args ...)   fprintf(MSG_OUT, args)
#define PRINT_ERROR(fmt, ...) PRINT_MSG("cn_serial_error: " fmt, ##__VA_ARGS__)


#if DEBUG
#define DEBUG_PRINT(args ...) fprintf(LOG, args)
#else
#define DEBUG_PRINT(args ...)
#endif


#if DEBUG
#define DEBUG_PRINT_PACKET(data, len)  do{ \
        for (unsigned char i=0; i < (len); i++) {\
            DEBUG_PRINT(" %02X", (data)[i]);\
        }\
        DEBUG_PRINT("\n");\
    }while(0)
#else
#define DEBUG_PRINT_PACKET(len, data)
#endif


#define PRINT_MEASURE(fmt, ...) PRINT_MSG("measures_debug: " fmt, __VA_ARGS__)


#endif // COMMON_H
