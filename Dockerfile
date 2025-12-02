FROM python:3.11-slim-bookworm

# Install system dependencies required by OpenCV and MediaPipe
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    jq \
    tzdata \
    curl \
    ca-certificates \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libgfortran5 \
    libavcodec59 \
    libavformat59 \
    libswscale6 \
    libavutil57 \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables to suppress FFmpeg logs
ENV FFREPORT=0
ENV AV_LOG_FORCE_NOCOLOR=1
ENV OPENCV_FFMPEG_LOGLEVEL=-8

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Create models directory
RUN mkdir -p /app/models

# Copy Google Gesture Recognizer model
COPY models/gesture_recognizer.task /app/models/

# Copy application code
COPY src/ /app/src/
COPY main.py config.py suppress_ffmpeg_logs.py test_startup.py /app/

# Copy run script
COPY run.sh /
RUN chmod a+x /run.sh

# Make test script executable
RUN chmod a+x /app/test_startup.py

CMD ["/run.sh"]
