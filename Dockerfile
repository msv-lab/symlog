FROM ubuntu:20.04
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
        python \
        sqlite3 \
        zlib1g-dev \
        wget \
        unzip \
        lsb-release \
        python3-pip

RUN wget https://github.com/souffle-lang/souffle/archive/refs/tags/2.1.zip \
    && unzip 2.1.zip \
    && cd souffle-2.1 \
    && cmake -S . -B build -DCMAKE_INSTALL_PREFIX=/usr \
    && cmake --build build --target install

COPY requirements.txt /tmp/requirements.txt

RUN python3 -m pip install -r /tmp/requirements.txt

RUN mkdir -p /symlog

COPY src/souffle.py /symlog/souffle.py

WORKDIR /symlog
