# Start with ROS Jazzy and ubuntu Noble
FROM ros:jazzy-ros-core-noble

# Install some basic utilities
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install micromamba
RUN curl -L https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xvj -C /usr/local/bin/ --strip-components=1 bin/micromamba

# Create directories for micromamba environment and cache
RUN mkdir -p /opt/conda/envs && mkdir -p /root/.conda/pkgs

# Copy the environment.yml file to the container
COPY environment.yml /tmp/environment.yml

# Create the micromamba environment using the environment.yml file
RUN micromamba create -y -n myenv -f /tmp/environment.yml && \
    micromamba clean --all --yes

# Set the micromamba environment as the default
ENV PATH /opt/conda/envs/myenv/bin:$PATH

# Set entrypoint 
COPY ./entrypoint.sh /
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

CMD ["bash"]
