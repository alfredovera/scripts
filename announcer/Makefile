# Makefile for announcer
test:
	go test -v -race -cover ./...

test-terse:
	go test -race -cover ./...

lint:
	golangci-lint run

build:
	go build -o announcer . 

build-linux:
	GOOS=linux GOARCH=amd64 go build -o announcer .

clean:
	rm -f announcer
