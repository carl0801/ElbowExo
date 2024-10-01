# Start with ROS Foxy and Ubuntu Focal
FROM osrf/ros:foxy-desktop

# Install some basic utilities
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    bzip2 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install micromamba
RUN curl -L https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xvj -C /usr/local/bin/ --strip-components=1 bin/micromamba && \
    chmod +x /usr/local/bin/micromamba

# Create directories for micromamba environment and cache
RUN mkdir -p /opt/conda/envs && mkdir -p /root/.conda/pkgs

# Set the MAMBA_ROOT_PREFIX environment variable
ENV MAMBA_ROOT_PREFIX=/opt/conda

# Copy the environment.yml file to the container
COPY environment.yml /tmp/environment.yml

# Create the micromamba environment using the environment.yml file
RUN micromamba create -y -n myenv -f /tmp/environment.yml && \
    micromamba clean --all --yes

# Set the micromamba environment as the default
ENV PATH=/opt/conda/envs/myenv/bin:$PATH

# Install rust
ENV RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    PATH=/usr/local/cargo/bin:$PATH \
    RUST_VERSION=1.81.0

RUN set -eux; \
    dpkgArch="$(dpkg --print-architecture)"; \
    case "${dpkgArch##*-}" in \
        amd64) rustArch='x86_64-unknown-linux-gnu'; rustupSha256='6aeece6993e902708983b209d04c0d1dbb14ebb405ddb87def578d41f920f56d' ;; \
        armhf) rustArch='armv7-unknown-linux-gnueabihf'; rustupSha256='3c4114923305f1cd3b96ce3454e9e549ad4aa7c07c03aec73d1a785e98388bed' ;; \
        arm64) rustArch='aarch64-unknown-linux-gnu'; rustupSha256='1cffbf51e63e634c746f741de50649bbbcbd9dbe1de363c9ecef64e278dba2b2' ;; \
        i386) rustArch='i686-unknown-linux-gnu'; rustupSha256='0a6bed6e9f21192a51f83977716466895706059afb880500ff1d0e751ada5237' ;; \
        ppc64el) rustArch='powerpc64le-unknown-linux-gnu'; rustupSha256='079430f58ad4da1d1f4f5f2f0bd321422373213246a93b3ddb53dad627f5aa38' ;; \
        s390x) rustArch='s390x-unknown-linux-gnu'; rustupSha256='e7f89da453c8ce5771c28279d1a01d5e83541d420695c74ec81a7ec5d287c51c' ;; \
        *) echo >&2 "unsupported architecture: ${dpkgArch}"; exit 1 ;; \
    esac; \
    url="https://static.rust-lang.org/rustup/archive/1.27.1/${rustArch}/rustup-init"; \
    wget "$url"; \
    echo "${rustupSha256} *rustup-init" | sha256sum -c -; \
    chmod +x rustup-init; \
    ./rustup-init -y --no-modify-path --profile minimal --default-toolchain $RUST_VERSION --default-host ${rustArch}; \
    rm rustup-init; \
    chmod -R a+w $RUSTUP_HOME $CARGO_HOME; \
    rustup --version; \
    cargo --version; \
    rustc --version;

# Copy the workspace folder to the container
COPY . /workspace

# Set the working directory
WORKDIR /workspace/workspace/build

RUN cmake .. && make



# Set entrypoint
#COPY ./entrypoint.sh /
#RUN chmod +x /entrypoint.sh

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

#CMD ["bash"]
CMD ["./hello_world"]