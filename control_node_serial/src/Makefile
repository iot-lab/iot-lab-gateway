.PHONY: control_node_measures_oml.h
SCAFFOLD = "oml2-scaffold"

control_node_measures_oml.h: control_node_measures.rb
	$(SCAFFOLD) --oml $<
	@# remove _GNU_SOURCE, defined at compile time with _DEFAULT_SOURCE
	sed -i '/#define _GNU_SOURCE/d' $@
