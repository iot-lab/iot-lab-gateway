.PHONY: all run clean realclean gcovr
quiet-cmd = $(if $(VERB),$1,$(if $(2),@echo $2 && $1, @$1))


COV          = -fprofile-arcs -ftest-coverage
OMLFLAGS     = -Wl,-rpath,/usr/local/lib -loml2

GTEST_DIR    = utils/gtest
CMOCKA_DIR   = utils/cmocka-0.4.1
CFLAGS      += -I$(GTEST_DIR)/include -I$(CMOCKA_DIR)/include -I$(SRCDIR) $(COV)
CFLAGS      += $(CFLAGSOPT) -ftrapv -g
CFLAGS      += -Wno-aggregate-return -Wno-write-strings
CPPFLAGS    += $(CFLAGS)
CXXFLAGS    += -g -Wall -Wextra -pthread $(LDFLAGS)


SRCDIR       = ../src
OBJDIR       = obj
BINDIR       = bin
RESULTDIR    = results
DIRS         = $(OBJDIR) $(BINDIR) $(RESULTDIR)


SRCS         = $(wildcard $(SRCDIR)/*.c)
SRCTESTS     = $(sort $(wildcard *.c) empty_test.c)
TESTS        = $(SRCTESTS:%.c=$(BINDIR)/%)
TEST_RESULTS = $(SRCTESTS:%.c=$(RESULTDIR)/%.xml)

CMOCKA_OBJS = $(OBJDIR)/cmocka.o


all: $(DIRS) empty_test.c $(TESTS)

# empty_test contains all C files but does nothing
# file is here only to see coverage of all source files
empty_test.c: $(wildcard $(SRCDIR)/*.c) $(SRCS)
	@echo "Generating $@ file"
	@echo '#include <gtest/gtest.h>' > $@
	@find ../src/ -name '*.c' -exec basename '{}' \; | grep -v main.c | \
		sed 's/.*/#include "&"/' \
		>> $@


run: all $(TEST_RESULTS)

# gcovr_root_dir/fit-dev/gateway_code_python/control_node_serial/tests
GCOVRFLAGS  = --root '../../../../' -e '.*/tests'
coverage: run gcovr $(RESULTDIR)/c_code_coverage.xml
	$(call quiet-cmd, gcovr $(GCOVRFLAGS) -f '.*/gateway_code_python/', \
		"  GCOV  STDOUT")
	$(call quiet-cmd, gcovr $(GCOVRFLAGS) -b -f '.*/gateway_code_python/', \
		"  GCOV  STDOUT")


gcovr:
	@gcovr --version > /dev/null || { echo "Missing dependency 'gcovr'. Install it with "; \
		echo ""; \
		echo "    # pip install gcovr"; \
		echo ""; false ; }


$(RESULTDIR)/c_code_coverage.xml: $(TEST_RESULTS)
	$(call quiet-cmd, gcovr $(GCOVRFLAGS) -b -x -o $@, "  GCOV  $@")

$(TEST_RESULTS) : $(RESULTDIR)/%.xml : $(BINDIR)/%
	$(call quiet-cmd, ./$^ --gtest_output=xml:$@, "  $^")


$(TESTS): $(BINDIR)/% : $(OBJDIR)/%.o $(OBJDIR)/gtest_main.a $(CMOCKA_OBJS)
	$(call quiet-cmd, $(CXX) -lgcov $(CPPFLAGS) $^ $(CXXFLAGS) $(OMLFLAGS) -o $@, \
		"  CXX   $@")



$(OBJDIR)/%_test.o: %_test.c $(SRCS)
	$(call quiet-cmd, $(CXX) -c $(COV) $(CFLAGS) $< -o $@, "  CXX   $@")
$(OBJDIR)/%.o: $(SRCDIR)/%.c
	$(call quiet-cmd, $(CXX) -c $(COV) $(CFLAGS) $< -o $@, "  CXX   $@")

$(SRCTESTS): %: $(SRCS)



$(DIRS):%:
	$(call quiet-cmd, mkdir -p $(@),)
clean:
	rm -rf $(GTEST_LIBS) $(OBJDIR) $(BINDIR)
realclean: clean
	rm -rf $(RESULTDIR) empty_test.c

$(CMOCKA_OBJS) : $(OBJDIR)/%.o: $(CMOCKA_DIR)/src/%.c $(CMOCKA_DIR)/include/%.h
	$(call quiet-cmd, $(CXX) -c $(COV) $(CFLAGS) $< -o $@, "  CXX   $@")

GTEST_HEADERS  = $(GTEST_DIR)/include/gtest/*.h
GTEST_HEADERS += $(GTEST_DIR)/include/gtest/internal/*.h
GTEST_SRCS_ = $(GTEST_DIR)/src/*.cc $(GTEST_DIR)/src/*.h $(GTEST_HEADERS)
GTEST_OBJS = $(OBJDIR)/gtest_main.o $(OBJDIR)/gtest-all.o

$(GTEST_OBJS) : $(OBJDIR)/%.o : $(GTEST_DIR)/src/%.cc $(GTEST_SRCS_)
	$(call quiet-cmd, $(CXX) -I$(GTEST_DIR) $(CPPFLAGS) $(CXXFLAGS) \
		-c $< -o $@, "  CXX   $@")

$(OBJDIR)/gtest.a : $(OBJDIR)/gtest-all.o
	$(call quiet-cmd, $(AR) $(ARFLAGS) $@ $^, "  AR    $@")

$(OBJDIR)/gtest_main.a : $(OBJDIR)/gtest-all.o $(OBJDIR)/gtest_main.o
	$(call quiet-cmd, $(AR) $(ARFLAGS) $@ $^, "  AR    $@")

