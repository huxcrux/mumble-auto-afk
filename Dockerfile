# Stage 1: Build stage
FROM python:3.12-slim

WORKDIR /app

# Install system tools needed for build
RUN apt-get update && apt-get install -y \
    wget \
    build-essential \
    libssl-dev \
    libbz2-dev \
    && rm -rf /var/lib/apt/lists/*

# Install pip packages to a custom prefix
COPY requirements.txt ./
COPY main.py /app/main.py
RUN pip install --no-cache-dir -r requirements.txt

# Add /install/bin to PATH and compile the ICE interface
RUN wget -O MumbleServer.ice https://raw.githubusercontent.com/mumble-voip/mumble/refs/heads/1.5.x/src/murmur/MumbleServer.ice && \
    slice2py MumbleServer.ice && \
    rm MumbleServer.ice

CMD ["python3", "main.py"]
