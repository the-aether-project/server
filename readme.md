# The Aether Server

## Usage

First, ensure all [`requirements`](./requirements.txt) are installed via

```sh
$ python -m pip install -R requirements.txt
```

Make sure your .env file looks something like this.
```sh

DB_NAME=aether
DB_USER=root
DB_PASSWORD=secret
DB_HOST=localhost
DB_PORT=5432
USE_DATABASE=1

GITHUB_CLIENT_SECRET="client536secret163githubf96"
GITHUB_CLIENT_ID="IvixUGITUHB_CLIENT_IDXE"

JWT_SECRET="secret_is_i_love_you_secretly"
JWT_EXPIRY= 10 #minutes

```

Then, use the following command to start the webserver.

```sh
$ python -m aiohttp.web -H 0.0.0.0 -P 7878 aether_server:create_app
```

Temporarily run docker image of postgres
```sh
docker run -d   --network="host"   -e POSTGRES_PASSWORD=secret   -e POSTGRES_USER=root   -e POSTGRES_DB=aether   -v /path/to/host/data:/var/lib/postgresql/data   postgres
```
