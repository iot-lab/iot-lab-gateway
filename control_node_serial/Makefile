TARGET     = control_node_serial_interface
CC         = gcc


# VERB = 1
quiet-cmd = $(if $(VERB),$1,$(if $(2),@echo $2 && $1, @$1))

WARNINGS  += -Werror
WARNINGS  += -Wall -Wextra
WARNINGS  += -Wpointer-arith -Wbad-function-cast
WARNINGS  += -Wcast-align -Waggregate-return -Wmissing-prototypes
WARNINGS  += -Wmissing-declarations

#  COV        = -fprofile-arcs -ftest-coverage
#  PROF       = -pg
DEP_RULES  = -MMD -MD -MF $(OBJDIR)/$*.d


CFLAGS    += -std=c99 -g -O3 -fstrict-aliasing
CFLAGS    += $(WARNINGS) $(COV) $(PROF) $(DEP_RULES) $(LIBS) -pthread
LDFLAGS   += $(CFLAGS) -lpthread

SRCS       = $(wildcard $(SRCDIR)/*.c)
OBJS       = $(SRCS:$(SRCDIR)/%.c=$(OBJDIR)/%.o)
DEPS       = $(SRCS:$(SRCDIR)/%.c=$(OBJDIR)/%.d)

SRCDIR     = src
OBJDIR     = obj

.PHONY: all clean realclean run test
.DEFAULT: all

all: $(OBJDIR) $(TARGET)

run: all
	./$(TARGET)
test: all
	make -C tests --no-print-directory run

$(TARGET): $(OBJS)
	$(call quiet-cmd, $(CC) -o $@ $(LDFLAGS) $^,   "  LD      $@")

$(OBJDIR)/%.o : $(SRCDIR)/%.c Makefile
	$(call quiet-cmd, $(CC) -c $(CFLAGS) $< -o $@, "  CC      $@")

$(OBJDIR):
	$(call quiet-cmd, mkdir -p $(@),)



clean:
	rm -rf $(OBJS) $(DEPS)
	make -C tests --no-print-directory clean
realclean: clean
	rm -rf $(TARGET)
	make -C tests --no-print-directory realclean
-include $(DEPS)

