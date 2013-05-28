TARGET     = control_node_interface
CC         = gcc


WARNINGS  += -Wpointer-arith -Wbad-function-cast
WARNINGS  += -Wcast-align -Wsign-compare -Waggregate-return -Wmissing-prototypes
WARNINGS  += -Wmissing-declarations

COV        = -fprofile-arcs -ftest-coverage
PROF       = -pg

CFLAGS     = -g -O2 $(WARNINGS) $(COV) $(PROF)
LDFLAGS    = $(CFLAGS)


SRCS       = $(wildcard *.c)
OBJS       = $(SRCS:.c=.o)

.PHONY: all clean realclean


all: $(TARGET)

clean:
	rm -rf $(OBJS)
realclean: clean
	rm -rf $(TARGET)


$(TARGET): $(OBJS)
	gcc -o $@ $(LDFLAGS) $<


