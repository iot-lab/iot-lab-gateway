TARGET     = control_node_interface
CC         = gcc


WARNINGS  += -Wall -Wextra
WARNINGS  += -Wpointer-arith -Wbad-function-cast
WARNINGS  += -Wcast-align -Wsign-compare -Waggregate-return -Wmissing-prototypes
WARNINGS  += -Wmissing-declarations

COV        = -fprofile-arcs -ftest-coverage
PROF       = -pg
DEP_RULES  = -MMD -MD -MF $(basename $@).d


CFLAGS    += -std=c99 -g -O3 -fstrict-aliasing
CFLAGS    += $(WARNINGS) $(COV) $(PROF) $(DEP_RULES) $(LIBS) -pthread
LDFLAGS   += $(CFLAGS) -lpthread

SRCS       = $(wildcard *.c)
OBJS       = $(SRCS:.c=.o)
DEPS       = $(SRCS:.c=.d)

.PHONY: all clean realclean run
.DEFAULT: all

all: $(TARGET)

run: all
	./$(TARGET)

$(TARGET): $(OBJS)
	$(CC) -o $@ $(LDFLAGS) $^

%.o : %.c Makefile
	$(CC) -c $(CFLAGS) $< -o $@



clean:
	rm -rf $(OBJS) $(DEPS)
realclean: clean
	rm -rf $(TARGET)
-include $(DEPS)

