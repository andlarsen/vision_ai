FROM python:3.11-slim

# Install system dependencies for OpenCV and webcam
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libv4l-dev \
    v4l-utils \
    && rm -rf /var/lib/apt/lists/*

# Qt fonts
RUN apt-get update && apt-get install -y \
    fontconfig \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY main.py .

CMD ["python", "main.py"]