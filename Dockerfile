FROM ubuntu:20.04
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt install software-properties-common -y && \
    add-apt-repository -y ppa:deadsnakes/ppa && \
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
        python3.10 \
        sqlite3 \
        zlib1g-dev \
        wget \
        unzip \
        lsb-release \
        curl \
        vim

RUN wget https://github.com/souffle-lang/souffle/archive/refs/tags/2.1.zip \
    && unzip 2.1.zip \
    && cd souffle-2.1 \
    && cmake -S . -B build -DCMAKE_INSTALL_PREFIX=/usr \
    && cmake --build build --target install -j8

RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10

COPY requirements.txt /tmp/requirements.txt

RUN python3.10 -m pip install -r /tmp/requirements.txt

RUN mkdir -p /symlog

COPY src /symlog/src
COPY digger_data /symlog/digger_data
COPY run_tup_expl_example.sh /symlog/run_tup_expl_example.sh

WORKDIR /symlog
