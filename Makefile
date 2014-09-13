CC = gcc
CXX = g++
AR = ar
PYTHON = python3

SCINTILLA_DIR=./scintilla
SCINTILLA_LIB=$(SCINTILLA_DIR)/bin/scintilla.a

# TODO: ADD Wall
CFLAGS = $(shell pkg-config --cflags gtk+-3.0) -O2 -I$(SCINTILLA_DIR)/include -Isrc -DGTK
LDFLAGS = $(shell pkg-config --libs gtk+-3.0) -L.

generated = src/gtkscintilla.c src/gtkscintilla.h
templates = $(foreach file,$(generated), $(file).template)
generator = generator.py

test_source = src/test.cpp
marshal_files = marshal.list src/marshal.h src/marshal.c

source := $(generated) $(marshal_files)
source := $(filter %.c %.h, $(source))

objs := $(patsubst src/%.c,%.o,$(filter %.c,$(source)))
dynamic_lib = libgtkscintilla3.so

all: $(dynamic_lib) test
$(SCINTILLA_LIB):
	make -C $(SCINTILLA_DIR)/gtk GTK3=1

generate_files: $(templates) $(generator)
	$(PYTHON) $(generator) --long_names

$(generated): generate_files

test: $(test_source) $(dynamic_lib)
	$(CXX) -o test $(CFLAGS) $(LDFLAGS) $(test_source) -lgtkscintilla3 -Wl,-rpath,.

#TODO: improve this
%.o : src/%.c $(filter %.h, $(source))
	$(CC) -c -fpic $(CFLAGS) $< -o $@

$(dynamic_lib): $(objs) $(SCINTILLA_LIB)
	$(CXX) -shared -o $(dynamic_lib) $(LDFLAGS) $(objs) $(SCINTILLA_LIB) -Wl,-soname,libgtkscintilla3.so

marshal.list: $(generator)
	$(PYTHON) $(generator) --mode marshal

src/marshal.h: marshal.list
	glib-genmarshal --header --prefix="gtkscintilla_marshal" marshal.list > $@

src/marshal.c: marshal.list
	glib-genmarshal --body --prefix="gtkscintilla_marshal" marshal.list > $@

clean:
	-rm test *.o *.so
	-rm $(generated)

cleanall: clean
	make -C $(SCINTILLA_DIR)/gtk clean
	-rm $(marshal_files)
