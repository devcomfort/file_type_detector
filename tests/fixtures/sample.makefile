.PHONY: all clean

all: build

build:
	gcc -o main main.c

clean:
	rm -f main
