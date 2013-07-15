#ifndef SERIAL_H
#define SERIAL_H

struct pkt {
        unsigned int len;
        unsigned char data[2048];
};

extern int configure_tty(char *tty_path);

extern void receive_data(int fd, unsigned char *rx_buff, size_t len,
                void (*handle_pkt)(struct pkt*));

#endif // SERIAL_H
