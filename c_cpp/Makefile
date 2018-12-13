# Set the variables that GNU Make uses
CC = gcc
CFLAGS = -g -Wall -I/usr/include/
LDFLAGS = -g -L. -L/usr/lib64/
LDLIBS = -lgsl -lgslcblas -lm

# Make will run the command like this for each .c file:
# $(CC) $(CFLAGS) $(LDFLAGS) <filename>.c $(LDLIBS) -o <filename>

SRC_FILES = $(wildcard *.c)
OBJ_FILES = $(patsubst %.c, %.o, $(SRC_FILES))
EXE_FILES = $(patsubst %.c, %,   $(SRC_FILES))

.PHONY: clean all

all: $(EXE_FILES)

# For each X.o file, if X.c is newer, run the command (compile the source file)
#%.o: %.c %.h
#	$(CC) -c -o $@ $<

## For each target X, if X.o exists and is newer than X, run the command (create the binary file)
#%: %.o
#	$(CC) -o $@ $<

clean:
	rm -f $(EXE_FILES) $(OBJ_FILES)
