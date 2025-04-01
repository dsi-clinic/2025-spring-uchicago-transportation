# Define constants

# general
mkfile_path := $(abspath $(firstword $(MAKEFILE_LIST)))
current_dir := $(notdir $(patsubst %/,%,$(dir $(mkfile_path))))
current_abs_path := $(subst Makefile,,$(mkfile_path))

# pipeline constants
# PROJECT_NAME
project_image_name := "2025-spring-uchicago-transportation"
project_container_name := "2025-spring-uchicago-transportation-container"
project_dir := "$(current_abs_path)"

# environment variables
# This will not be required for all projects
# include .env

# Build Docker image 
.PHONY: build-only run-interactive run-notebook

# Build Docker image 
build-only: 
	docker build -t $(project_image_name) -f Dockerfile "$(current_abs_path)"

run-interactive: build-only	
	docker run -it -v $(current_abs_path):/project -t $(project_image_name) /bin/bash

run-notebooks: build-only	
	docker run -v "$(current_abs_path)":/project -p 8888:8888 -t $(project_image_name) \
	jupyter lab --port=8888 --ip='*' --NotebookApp.token='' --NotebookApp.password='' \
	--no-browser --allow-root


