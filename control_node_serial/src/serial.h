#ifndef SERIAL_H
#define SERIAL_H

struct pkt {
        unsigned int len;
        unsigned int missing;
        unsigned int current_len;
        unsigned char data[2048];
};

extern int configure_tty(char *tty_path);

extern void start_listening(int fd, void (*handle_pkt)(struct pkt*));

#endif // SERIAL_H
