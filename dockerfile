# Start with ROS Foxy and Ubuntu Focal
FROM osrf/ros:foxy-desktop

# Install some basic utilities
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
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
ENV PATH /opt/conda/envs/myenv/bin:$PATH

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