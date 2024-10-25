FROM python:3

WORKDIR /usr/src/app

# install system requirements
RUN apt-get update && \ 
    apt-get install -y --no-install-recommends \
    libavformat-dev \
    libavcodec-dev \
    libavutil-dev \
    libswscale-dev \
    libswresample-dev \
    libavdevice-dev \
    libavfilter-dev \
    pkg-config \
    && apt-get clean \  
    && rm -rf /var/lib/apt/lists/*


COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD ["python", "-m", "aiohttp.web", "-H", "0.0.0.0", "-P", "7878", "aether_server:create_app"]
