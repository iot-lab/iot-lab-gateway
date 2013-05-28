TARGET     = control_node_interface
CC         = gcc


WARNINGS  += -Wall -Wextra
WARNINGS  += -Wpointer-arith -Wbad-function-cast
WARNINGS  += -Wcast-align -Wsign-compare -Waggregate-return -Wmissing-prototypes
WARNINGS  += -Wmissing-declarations

COV        = -fprofile-arcs -ftest-coverage
PROF       = -pg

CFLAGS     = -std=c99 -g -O3 -fstrict-aliasing $(WARNINGS) $(COV) $(PROF)
LDFLAGS    = $(CFLAGS)


 #   -O2 activates -fstrict-aliasing and -Wall is supposed


SRCS       = $(wildcard *.c)
OBJS       = $(SRCS:.c=.o)

.PHONY: all clean realclean run
.DEFAULT: all

all: $(TARGET)

run: all
	./$(TARGET)


clean:
	rm -rf $(OBJS)
realclean: clean
	rm -rf $(TARGET)


$(TARGET): $(OBJS)
	gcc -o $@ $(LDFLAGS) $<


