FROM python:3.12

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD ["python", "-m", "aiohttp.web", "-H", "0.0.0.0", "-P", "7878", "aether_server:create_app"]
