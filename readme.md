# The Aether Server

## Usage

First, ensure all [`requirements`](./requirements.txt) are installed via

```sh
$ python -m pip install -R requirements.txt
```

Then, use the following command to start the webserver.

```sh
$ python -m aiohttp.web -H 0.0.0.0 -P 7878 aether_server:create_app
```

Temporarily run docker image of postgres
```sh
docker run -d   --network="host"   -e POSTGRES_PASSWORD=secret   -e POSTGRES_USER=root   -e POSTGRES_DB=aether   -v /path/to/host/data:/var/lib/postgresql/data   postgres
```
