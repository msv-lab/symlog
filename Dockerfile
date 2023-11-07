FROM ubuntu:22.04
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y \
        bison \
        build-essential \
        clang \
        cmake \
        doxygen \
        flex \
        g++ \
        git \
        libffi-dev \
        libncurses5-dev \
        libsqlite3-dev \
        make \
        mcpp \
        python3 \
        zlib1g-dev \
        wget \
        unzip \
        lsb-release \
        python3-pip \
        dpkg 


RUN wget -P /tmp https://github.com/souffle-lang/souffle/releases/download/2.2/x86_64-ubuntu-2104-souffle-2.2-Linux.deb \
    && dpkg -i /tmp/x86_64-ubuntu-2104-souffle-2.2-Linux.deb \
    && apt-get install -y -f \
    && rm /tmp/x86_64-ubuntu-2104-souffle-2.2-Linux.deb


COPY requirements.txt /tmp/requirements.txt

WORKDIR /symlog

COPY . /symlog

ENV PYTHONPATH /symlog

RUN python3 -m pip install -r /tmp/requirements.txt \
    && python3 -m pip install -e .


