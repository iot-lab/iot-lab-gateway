#ifndef OML_MEASURES_H
#define OML_MEASURES_H

int oml_measures_start(char *oml_config_file_path);
int oml_measures_stop(void);

void oml_measures_consumption(uint64_t timestamp_s, uint32_t timestamp_us, double current, double voltage, double power);
void oml_measures_radio(uint64_t timestamp_s, uint32_t timestamp_us, int32_t rssi, int32_t lqi);


#endif // OML_MEASURES_H
