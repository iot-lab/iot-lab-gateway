TARGET     = control_node_interface
CC         = gcc


# VERB = 1
quiet-cmd = $(if $(VERB),$1,$(if $(2),@echo $2 && $1, @$1))

WARNINGS  += -Wall -Wextra
WARNINGS  += -Wpointer-arith -Wbad-function-cast
WARNINGS  += -Wcast-align -Waggregate-return -Wmissing-prototypes
WARNINGS  += -Wmissing-declarations

#  COV        = -fprofile-arcs -ftest-coverage
#  PROF       = -pg
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
	$(call quiet-cmd, $(CC) -o $@ $(LDFLAGS) $^,   "  LD      $@")

%.o : %.c Makefile
	$(call quiet-cmd, $(CC) -c $(CFLAGS) $< -o $@, "  CC      $@")



clean:
	rm -rf $(OBJS) $(DEPS)
realclean: clean
	rm -rf $(TARGET)
-include $(DEPS)

