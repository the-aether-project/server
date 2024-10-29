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
