#ifndef OML_MEASURES_H
#define OML_MEASURES_H

int oml_measures_start(char *oml_config_file_path);
int oml_measures_stop(void);

void oml_measures_consumption(uint32_t timestamp_s, uint32_t timestamp_us,
                              double power, double voltage, double current);
void oml_measures_radio(uint32_t timestamp_s, uint32_t timestamp_us,
                        uint32_t channel, int32_t rssi);


#endif // OML_MEASURES_H
