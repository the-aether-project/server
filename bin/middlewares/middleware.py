from aiohttp import web
from .exceptions import BadRequestError, NotFoundError


def create_error_middleware():
    @web.middleware
    async def error_middleware(request, handler):
        try:
            return await handler(request)
        except BadRequestError as e:
            request.protocol.logger.exception(f"Bad Request Found : {str(e)}")
            return web.json_response(
                {"Error": e.message, "Status": e.status_code}, status=e.status_code
            )
        except NotFoundError as e:
            request.protocol.logger.exception(f"Request Not Found : {str(e)}")
            return web.json_response(
                {
                    "Error": e.message,
                    "Status": e.status_code,
                },
                status=e.status_code,
            )

        except Exception as e:
            request.protocol.logger.exception(
                f"Unhandled, Intenal server error : {str(e)}"
            )
            return web.json_response(
                {
                    "Error": str(e),
                    "Status": e.status_code if hasattr(e, "status_code") else 500,
                },
                status=e.status_code if hasattr(e, "status_code") else 500,
            )

    return error_middleware


def setup_middleware(app):
    error_middlware = create_error_middleware()
    app.middlewares.append(error_middlware)
