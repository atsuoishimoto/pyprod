CC=gcc
CFLAGS=-I.
DEPS = hello.h
OBJS = main.o hello.o
.PHONY: clean

%.o: %.c $(DEPS)
	$(CC) -c -o $@ $< $(CFLAGS)

hello.exe: $(OBJS)
	$(CC) -o $@ $^

clean:
	rm -f $(OBJS) hello.exe

