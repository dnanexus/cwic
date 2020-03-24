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
    dxpy

# Install dxfuse
RUN wget https://github.com/dnanexus/dxfuse/releases/download/v0.20/dxfuse-linux -P /usr/local/bin/ \
    && mv /usr/local/bin/dxfuse-linux /usr/local/bin/dxfuse \
    && chmod +x /usr/local/bin/dxfuse

RUN mkdir /project /scratch

CMD ["/bin/bash"]

WORKDIR /home/dnanexus
ENV HOME=/home/dnanexus

# Set cwic prompt
RUN echo 'PS1="$(tput setaf 3)$(tput bold)root@cwic:\\w# $(tput sgr0)"' >> /etc/bash.bashrc

# Update stty size upon login to the container (stty size is used by dx printing utility)
RUN echo 'stty columns $COLUMNS; stty rows $LINES' >> /etc/bash.bashrc
