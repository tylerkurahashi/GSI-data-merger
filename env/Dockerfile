FROM ghcr.io/osgeo/gdal:ubuntu-full-3.8.5

# config
ENV DEBIAN_FRONTEND=noninteractive
SHELL ["/bin/bash", "-c"]

# dependency
RUN apt-get update && apt-get upgrade -y

RUN apt-get update --fix-missing && apt-get install -y --no-install-recommends\     
        build-essential \
        libfreetype6-dev \
        libpng-dev \
        libzmq3-dev \
        python3-dev \
        libsm6 \
        vim \
        git \
        curl \
        wget \
        zip \
        zsh \
        pip \
        neofetch \
        openssh-server \
        htop \
        screen \
        && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* 

RUN pip install -U pip
RUN pip install --upgrade pip setuptools
COPY env/requirements.txt .
RUN pip install -r requirements.txt
ENV PYTHONPATH $PYTHONPATH:/workspace

# path
RUN mkdir /workspace
WORKDIR /workspace

ENTRYPOINT [ "sleep", "infinity" ]