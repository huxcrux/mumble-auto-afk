# Makefile

# Variables
IMAGE_NAME := github.com/huxcrux/mumble-auto-afk

.PHONY: run build

# Run the Python file
run:
	python3 main.py

# Build the Docker container
build:
	podman build -t $(IMAGE_NAME) .
