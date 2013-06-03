#ifndef SERIAL_H
#define SERIAL_H

struct pkt {
        unsigned int len;
        unsigned int missing;
        unsigned int current_len;
        unsigned char data[2048];
};

int configure_tty(int fd);

void start_listening(int fd, void (*decode_pkt)(struct pkt*));

#endif // SERIAL_H
