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

#ifndef OML_MEASURES_H
#define OML_MEASURES_H

int oml_measures_start(char *oml_config_file_path, int print_measures);
int oml_measures_stop(void);

void oml_measures_consumption(uint32_t timestamp_s, uint32_t timestamp_us,
                              double power, double voltage, double current);
void oml_measures_radio(uint32_t timestamp_s, uint32_t timestamp_us,
                        uint32_t channel, int32_t rssi);
void oml_measures_sniffer(uint32_t timestamp_s, uint32_t timestamp_us,
                          uint32_t channel, int32_t rssi, uint32_t lqi,
                          uint8_t crc_ok, uint32_t length);
void oml_measures_event(uint32_t timestamp_s, uint32_t timestamp_us,
                        uint32_t value, const char* name);


#endif // OML_MEASURES_H
