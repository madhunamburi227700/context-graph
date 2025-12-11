# Base Image
FROM ubuntu:22.04

# Set environment variable (before apt)
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies + sudo + nodejs
RUN apt-get update && apt-get install -y \
    sudo \
    git \
    curl \
    wget \
    ca-certificates \
    build-essential \
    python3 \
    python3-pip \
    vim \
    tree \
    grep \
    ripgrep \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspace

COPY . /workspace
# Default command
CMD ["/bin/bash"]
