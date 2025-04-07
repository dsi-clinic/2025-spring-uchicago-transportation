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

# Streamlit port (can be overridden from command line)
STREAMLIT_PORT ?= 8501


# Build Docker image 
.PHONY: build-only run-interactive run-notebook \
		data-process-docker data-pipeline run-dashboard

# Build Docker image 
build-only: 
	docker build -t $(project_image_name) -f Dockerfile "$(current_abs_path)"

run-interactive: build-only	
	docker run -it -v $(current_abs_path):/project -p $(STREAMLIT_PORT):8501 \
	-t $(project_image_name) /bin/bash

run-notebooks: build-only	
	docker run -v "$(current_abs_path)":/project -p 8888:8888 -t $(project_image_name) \
	jupyter lab --port=8888 --ip='*' --NotebookApp.token='' --NotebookApp.password='' \
	--no-browser --allow-root

run-data-pipeline: build-only
	docker run -v $(current_abs_path):/project -t $(project_image_name) \
	python src/utils/data_cleaning.py

data-pipeline:
	python src/utils/data_cleaning.py

run-dashboard: build-only
	docker run -v "$(current_abs_path)":/project -p $(STREAMLIT_PORT):8501 --name $(project_container_name) -t $(project_image_name) \
	streamlit run /project/dashboard/app.py --server.address=0.0.0.0 --server.port=8501	