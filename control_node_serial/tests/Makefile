.PHONY: all run clean realclean
quiet-cmd = $(if $(VERB),$1,$(if $(2),@echo $2 && $1, @$1))


COV          = -fprofile-arcs -ftest-coverage

GTEST_DIR    = utils/gtest
CFLAGS      += -I$(GTEST_DIR)/include -I$(SRCDIR) $(COV)
CFLAGS      += $(CFLAGSOPT)
CFLAGS      += -Wno-aggregate-return -Wno-write-strings
CPPFLAGS    += $(CFLAGS)
CXXFLAGS    += -g -Wall -Wextra -pthread


SRCDIR       = ../src
OBJDIR       = obj
BINDIR       = bin
RESULTDIR    = results
DIRS         = $(OBJDIR) $(BINDIR) $(RESULTDIR)


SRCTESTS     = $(wildcard *.c)
TESTS        = $(SRCTESTS:%.c=$(BINDIR)/%)
TEST_RESULTS = $(SRCTESTS:%.c=$(RESULTDIR)/%.xml)


all: $(DIRS) $(TESTS)


run: all $(TEST_RESULTS) $(RESULTDIR)/c_code_coverage.xml


$(RESULTDIR)/c_code_coverage.xml: all
	$(call quiet-cmd, gcovr -x -e '/usr' -e '.*/tests' \
		-f'.*/gateway_code_python' >$@, "  GCOV    $@")
	$(call quiet-cmd, gcovr -e '/usr' -e '.*/tests' \
		-f'.*/gateway_code_python', "  GCOV    STDOUT")

$(TEST_RESULTS) : $(RESULTDIR)/%.xml : $(BINDIR)/%
	$(call quiet-cmd, ./$^ --gtest_output=xml:$@, "  $^")


$(TESTS): $(BINDIR)/% : $(OBJDIR)/%.o $(OBJDIR)/gtest_main.a
	$(call quiet-cmd, $(CXX) -lgcov $(CPPFLAGS) $(CXXFLAGS) $^ -o $@, "  CXX    $@")


$(OBJDIR)/%_test.o: %_test.c
	$(call quiet-cmd, $(CXX) -c $(COV) $(CFLAGS) $< -o $@, "  CXX      $@")
$(OBJDIR)/%.o: $(SRCDIR)/%.c
	$(call quiet-cmd, $(CXX) -c $(COV) $(CFLAGS) $< -o $@, "  CXX      $@")


$(DIRS):%:
	$(call quiet-cmd, mkdir -p $(@),)
clean:
	rm -rf $(GTEST_LIBS) $(OBJDIR) $(BINDIR)
realclean: clean
	rm -rf $(RESULTDIR)


GTEST_HEADERS  = $(GTEST_DIR)/include/gtest/*.h
GTEST_HEADERS += $(GTEST_DIR)/include/gtest/internal/*.h
GTEST_SRCS_ = $(GTEST_DIR)/src/*.cc $(GTEST_DIR)/src/*.h $(GTEST_HEADERS)
GTEST_OBJS = $(OBJDIR)/gtest_main.o $(OBJDIR)/gtest-all.o

$(GTEST_OBJS) : $(OBJDIR)/%.o : $(GTEST_DIR)/src/%.cc $(GTEST_SRCS_)
	$(call quiet-cmd, $(CXX) -I$(GTEST_DIR) $(CPPFLAGS) $(CXXFLAGS) -c $< -o $@, "  CXX     $@")

$(OBJDIR)/gtest.a : $(OBJDIR)/gtest-all.o
	$(call quiet-cmd, $(AR) $(ARFLAGS) $@ $^, "  AR    $@")

$(OBJDIR)/gtest_main.a : $(OBJDIR)/gtest-all.o $(OBJDIR)/gtest_main.o
	$(call quiet-cmd, $(AR) $(ARFLAGS) $@ $^, "  AR    $@")

