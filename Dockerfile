FROM jupyter/r-notebook

ENV GRANT_SUDO=yes

# Install Tensorflow & RPY2
RUN conda install --quiet --yes 'tensorflow=1.3*' 'keras=2.0*' 'rpy2' && \
    conda clean -tipsy && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/$NB_USER

# Copy repo into ${HOME}, make user own $HOME
USER root
COPY . ${HOME}
RUN chown -R ${NB_USER} ${HOME}
RUN apt-get update && apt-get install -y graphviz
USER ${NB_USER}

## Install dependencies if specified
RUN if [ -f install.R ]; then R --quiet -f install.R; fi
RUN if [ -f requirements.txt ]; then pip install -U -r requirements.txt; fi
    