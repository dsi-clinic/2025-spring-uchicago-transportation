# This is a basic docker image for use in the clinic

FROM jupyter/minimal-notebook:python-3.11

# Swith to root to update and install python dev tools
USER root
RUN apt update
RUN apt install -y python3-pip python3-dev

# Create working directory
WORKDIR /project

# Adjust permissions for everything within /project before switching back to $NB_UID
COPY --chown=$NB_UID:$NB_GID src ./src
COPY --chown=$NB_UID:$NB_GID pyproject.toml .
COPY --chown=$NB_UID:$NB_GID requirements.txt .

# Switch back to the non-root user before installing Python packages
USER $NB_UID

# Install Python 3 packages
RUN pip install --no-cache-dir -r requirements.txt

# install project as an editable package
RUN pip install -e .

CMD ["/bin/bash"]