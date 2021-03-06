FROM ubuntu:18.04

LABEL description="Base image used for Developer Workstation at DNAnexus"
LABEL maintainer="Ola Zalcman <azalcman@dnanexus.com>"

SHELL ["/bin/bash", "-c"]
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get clean \
    && apt-get update \
    && apt-get install -y \
        curl \
        gcc \
        fuse \
        git \
        jq \
        locales \
        locales-all \
        python3-pip \
        vim \
        wget \
    && rm -rf /var/lib/apt/lists/*

# Encoding settings
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8
ENV LC_CTYPE=en_US.UTF-8

# Set python3 as default python implementation
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1

# Install docker
RUN curl -fsSL get.docker.com -o get-docker.sh \
    && sh get-docker.sh

RUN pip3 install --no-cache-dir \
    dxpy==v0.305.0

# Install dxfuse
RUN wget https://github.com/dnanexus/dxfuse/releases/download/v0.23.2/dxfuse-linux -P /usr/local/bin/ \
    && mv /usr/local/bin/dxfuse-linux /usr/local/bin/dxfuse \
    && chmod +x /usr/local/bin/dxfuse

RUN mkdir -p /project /scratch /home/dnanexus /home/cwic

CMD ["/bin/bash"]

WORKDIR /home/cwic
ENV HOME=/home/cwic

# Set cwic prompt
RUN echo 'PS1="\001$(tput setaf 3)\002\001$(tput bold)\002root@cwic:\\w# \001$(tput sgr0)\002"' >> /etc/bash.bashrc

# Update stty size upon login to the container (stty size is used by dx printing
# functions for proper formatting), if COLUMNS and LINES variables are passed
RUN echo 'if [[ -n $COLUMNS ]]; then stty columns $COLUMNS; fi; if [[ -n $LINES ]]; then stty rows $LINES; fi' >> /etc/bash.bashrc
