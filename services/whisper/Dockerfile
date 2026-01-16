# Whisper.cpp Server Dockerfile
# Builds whisper.cpp from source and runs whisper-server

FROM ubuntu:22.04 AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Clone whisper.cpp
WORKDIR /whisper.cpp
RUN git clone https://github.com/ggerganov/whisper.cpp.git .

# Build whisper.cpp
RUN cmake -B build
RUN cmake --build build -j --config Release

# Download model
RUN mkdir -p models && \
    wget -O models/ggml-large-v3-turbo-q5_0.bin \
    https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo-q5_0.bin

# Runtime stage - smaller image
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /whisper.cpp

# Copy built binary, shared libs, and model from builder
COPY --from=builder /whisper.cpp/build/bin/whisper-server /whisper.cpp/build/bin/
COPY --from=builder /whisper.cpp/build/src/libwhisper.so* /usr/local/lib/
COPY --from=builder /whisper.cpp/build/ggml/src/libggml*.so* /usr/local/lib/
COPY --from=builder /whisper.cpp/models /whisper.cpp/models

# Update library cache
RUN ldconfig

EXPOSE 9000

# Start the server exactly like local setup
CMD ["./build/bin/whisper-server", "-m", "models/ggml-large-v3-turbo-q5_0.bin", "--port", "9000", "--host", "0.0.0.0"]
