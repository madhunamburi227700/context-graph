# Base Image
FROM ubuntu:22.04

# Avoid prompts during apt operations
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
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
    unzip \
    grep \
    ripgrep \
    maven \
    && rm -rf /var/lib/apt/lists/*

# -------------------- OPENJDK 19 SETUP --------------------
RUN mkdir -p /usr/lib/jvm \
    && curl -fSL "https://github.com/adoptium/temurin19-binaries/releases/download/jdk-19.0.2%2B7/OpenJDK19U-jdk_x64_linux_hotspot_19.0.2_7.tar.gz" -o /tmp/openjdk.tar.gz \
    && tar -xzf /tmp/openjdk.tar.gz -C /usr/lib/jvm \
    && rm /tmp/openjdk.tar.gz \
    && mv /usr/lib/jvm/jdk-19.0.2+7 /usr/lib/jvm/java-19-openjdk-amd64

# Set JAVA_HOME and PATH
ENV JAVA_HOME=/usr/lib/jvm/java-19-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:$PATH"

RUN java -version

# -------------------- NODE.JS + NPM + CDXGEN --------------------
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g @cyclonedx/cdxgen

RUN node -v && npm -v && cdxgen -v

# -------------------- UV SETUP (GLOBAL) --------------------
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && mv /root/.local/bin/uv /usr/local/bin/uv \
    && mv /root/.local/bin/uvx /usr/local/bin/uvx \
    && chmod +x /usr/local/bin/uv /usr/local/bin/uvx

RUN uv --version

# -------------------- GO 1.24.4 SETUP --------------------
RUN curl -fSL https://go.dev/dl/go1.24.4.linux-amd64.tar.gz -o /tmp/go.tar.gz \
    && tar -C /usr/local -xzf /tmp/go.tar.gz \
    && rm /tmp/go.tar.gz \
    && ln -s /usr/local/go/bin/go /usr/local/bin/go \
    && go version

# -------------------- DEPTREE SETUP --------------------
ENV GOPATH=/root/go
RUN mkdir -p $GOPATH/bin \
    && go install github.com/vc60er/deptree@latest \
    && ln -sf $GOPATH/bin/deptree /usr/local/bin/deptree \
    && deptree -v || echo "Deptree installed"

# -------------------- CYCLONEDX-GOMOD SETUP --------------------
RUN mkdir -p $GOPATH/bin \
    && go install github.com/CycloneDX/cyclonedx-gomod/cmd/cyclonedx-gomod@latest \
    && ln -sf $GOPATH/bin/cyclonedx-gomod /usr/local/bin/cyclonedx-gomod \
    && cyclonedx-gomod version || echo "cyclonedx-gomod installed"

# -------------------- WORKSPACE --------------------
WORKDIR /workspace

# Copy dependency files first for caching
COPY pyproject.toml uv.lock ./
RUN uv sync --no-install-project

# Copy application code
COPY . /workspace
RUN uv sync

# Command to run the application
CMD ["python3", "main.py"]
