# Minimal build for the netbook demo pack (compile on the target machine).
CC ?= gcc

.PHONY: all run clean

all: run

run: run.c
	$(CC) -O3 -o run run.c -lm

clean:
	rm -f run
