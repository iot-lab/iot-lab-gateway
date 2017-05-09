TARGET     = control_node_serial_interface
CC         ?= gcc


# VERB = 1
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

ifeq (1, $(DEBUG))
CFLAGS += -DDEBUG=1
endif

CFLAGS    += -std=c99 -g -O3 -fstrict-aliasing
CFLAGS    += $(WARNINGS) $(COV) $(PROF) $(DEP_RULES) $(LIBS) -pthread

# Define Feature Macros
CFLAGS    += -D_POSIX_C_SOURCE=200809L
CFLAGS    += -D_DEFAULT_SOURCE

OMLFLAGS  = -Wl,-rpath,/usr/local/lib -loml2 -locomm
LDFLAGS   += $(CFLAGS) -lpthread $(OMLFLAGS)

SRCS       = $(wildcard $(SRCDIR)/*.c)
OBJS       = $(SRCS:$(SRCDIR)/%.c=$(OBJDIR)/%.o)
DEPS       = $(SRCS:$(SRCDIR)/%.c=$(OBJDIR)/%.d)

SRCDIR     = src
OBJDIR     = obj

.PHONY: all clean realclean run test tests
.DEFAULT: all

all: $(OBJDIR) $(TARGET)


run: all
	./$(TARGET)

tests: test
test: all
	make -C tests --no-print-directory run
coverage: all
	make -C tests --no-print-directory coverage

.PHONY: $(SRCDIR)/control_node_measures_oml.h
$(SRCDIR)/control_node_measures_oml.h:
	make -C $(SRCDIR) control_node_measures_oml.h

$(TARGET): $(SRCDIR)/control_node_measures_oml.h $(OBJS)
	$(call quiet-cmd, $(CC) -o $@ $^ $(LDFLAGS),   "  LD      $@")

$(OBJDIR)/%.o : $(SRCDIR)/%.c Makefile
	$(call quiet-cmd, $(CC) -c $(CFLAGS) $< -o $@, "  CC      $@")

$(OBJDIR):
	$(call quiet-cmd, mkdir -p $(@),)



clean:
	rm -rf $(OBJDIR)/*
	make -C tests --no-print-directory clean
realclean: clean
	rm -rf $(TARGET)
	rm -rf $(OBJDIR)
	make -C tests --no-print-directory realclean
-include $(DEPS)

