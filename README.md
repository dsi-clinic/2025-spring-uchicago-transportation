# 2025-spring-uchicago-transportation

## Project Background

The UGo Shuttle program is a free shuttle service provided by the University of Chicago. Each UGo shuttle is equipped with a card reader, located just inside the door of the shuttle. All passengers are asked to tap their valid UChicago-issued ID on a card reader each time they board a UGo Shuttle. The card readers are used to collect information on the peak times and routes used by the various parts of the University community.

Working in collaboration with [uchicagoshuttles.com](uchicagoshuttles.com), the DSI is helping UChicago Transportation analyze their rider data and make informed decisions about the routes, stops, and schedules of UGo shuttles. The purpose of this quarter's work is to better understand rider waiting patterns with respect to time-of-day and location-specific effects. Specifically, we want to do the following:

- Identify a set of research questions and the variables that can answer them in the shuttle data
- Develop a data pipeline to extract relevant information from the shuttle data
- Create visualizations or dashboards to explain your findings

This project is being done in public under the terms of the [license](./LICENSE). 


## Project Goals

Important details in the first week:
- The data for this project is in a box folder that will be shared with you during the first week. Tag Nick or Tim in the channel to get access. **The data should NOT be stored in the repo, if this occurs it will significantly impact the final grade, it is a violation of the terms of service of its use.**
- During the first week start begin by downloading and exploring the data. Answer the following questions:
  - Which stop, on each line, has highest variance of time between arrivals?
  - Which stop, on each line, has the lowest variance of time between arrivals?
- Identify a set of key questions that would benefit planners and users of the service. Put these questions in a doc in the repository.


At the end of the quarter, it is expected that this repo will contain the following:
  - Code: 
    - `make dashboard` should start a streamlit, multi-page, dashboard showing the results of your analysis and visualizations.
    - (if required) `make data-process` should run a data processing script for taking the raw input data and creating those dashboards.
  - Write-up
    - A short document, which will be sent in the final email, describing the work that you have done. It should be ~3 pages long and cover:
      - The research questions you answered (and why you thought they were important). Please be specific about the questions and their answers.
      - Limitations in the data that you encountered and what would need to be fixed/updated.
  - **Note that the write-up is in addition to the requirements listed in the syllabus**

## Usage

### API Key
The 'Connector Bunching Map' dashboard requires Google Maps API key to function. For full functionality, API key has to be given for the dashboard to utilize.

1. Create .env file in the root directory.
2. In the .env file: GOOGLE_MAP_KEY= your_google_map_key

### Docker

### Docker & Make

We use `docker` and `make` to run our code. There are three built-in `make` commands:

* `make build-only`: This will build the image only. It is useful for testing and making changes to the Dockerfile.
* `make run-notebooks`: This will run a jupyter server which also mounts the current directory into `\program`.
* `make run-interactive`: This will create a container (with the current directory mounted as `\program`) and loads an interactive session. 

The file `Makefile` contains information about about the specific commands that are run using when calling each `make` statement.

### Developing inside a container with VS Code

If you prefer to develop inside a container with VS Code then do the following steps. Note that this works with both regular scripts as well as jupyter notebooks.

1. Open the repository in VS Code
2. At the bottom right a window may appear that says `Folder contains a Dev Container configuration file...`. If it does, select, `Reopen in Container` and you are done. Otherwise proceed to next step. 
3. Click the blue or green rectangle in the bottom left of VS code (should say something like `><` or `>< WSL`). Options should appear in the top center of your screen. Select `Reopen in Container`.


## Style
We use [`ruff`](https://docs.astral.sh/ruff/) to enforce style standards and grade code quality. This is an automated code checker that looks for specific issues in the code that need to be fixed to make it readable and consistent with common standards. `ruff` is run before each commit via [`pre-commit`](https://pre-commit.com/). If it fails, the commit will be blocked and the user will be shown what needs to be changed.

To check for errors locally, first ensure that `pre-commit` is installed by running `pip install pre-commit` followed by `pre-commit install`. Once installed, check for errors by running:
```
pre-commit run --all-files
```

## Repository Structure

### utils
Project python code

### notebooks
Contains short, clean notebooks to demonstrate analysis.

### data

All data should be obtained from uchicago Box. The information on how to access the data is available in this [README.md file](/data/README.md).

### output
Should contain work product generated by the analysis. Keep in mind that results should (generally) be excluded from the git repository.


## Group Members

Minjae Joh
johminjae@uchicago.edu

Leah Dimsu 
leahdimsu@uchicago.edu

Kristen Wallace
kwallace2@uchicago.edu

Luna Jian
jiany@uchicago.edu
