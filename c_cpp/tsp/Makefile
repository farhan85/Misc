# Set the variables that GNU Make uses
CC = gcc
CFLAGS = -g -Wall -I/usr/include/
LDFLAGS = -g -L. -L/usr/lib64/
LDLIBS = -lgsl -lgslcblas -lm

# $(CC) $(CFLAGS) < files >
# $(CC) $(LDFLAGS) < files > $(LDLIBS)

SRC_FILES = $(wildcard src/*.c)
HDR_FILES = $(wildcard *.h)
OBJ_FILES = $(patsubst %.c, %.o, $(SRC_FILES))

.PHONY: clean all

all: solve_tsp

solve_tsp: $(OBJ_FILES)
	$(CC) $(CFLAGS) $(LD_FLAGS) $(LDLIBS) -o $@ $^

%.o: %.c $(HDR_FILES)
	$(CC) $(CFLAGS) -c -o $@ $<

clean:
	rm -f $(OBJ_FILES)
