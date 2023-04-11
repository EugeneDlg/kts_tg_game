import typing

from aiohttp.web_exceptions import (
    HTTPBadRequest,
    HTTPConflict,
    HTTPForbidden,
    HTTPMethodNotAllowed,
    HTTPNotFound,
    HTTPServerError,
    HTTPUnauthorized,
    HTTPUnprocessableEntity,
)
from aiohttp.web_middlewares import middleware
from aiohttp_apispec import validation_middleware

from apps.api.utils import error_json_response, error_reason, error_text

if typing.TYPE_CHECKING:
    from apps.api.app import Application, Request

HTTP_ERROR_CODES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "not_implemented",
    409: "conflict",
    500: "internal_server_error",
}


@middleware
async def error_handling_middleware(request: "Request", handler):
    try:
        response = await handler(request)
        return response

    except HTTPUnprocessableEntity as e:
        return error_json_response(
            http_status=400,
            status=HTTP_ERROR_CODES[400],
            message=error_reason(e),
            data=error_text(e),
        )
    except HTTPBadRequest as e:
        return error_json_response(
            http_status=400,
            status=HTTP_ERROR_CODES[400],
            message=error_reason(e),
            data=error_text(e),
        )
    except HTTPUnauthorized as e:
        return error_json_response(
            http_status=401,
            status=HTTP_ERROR_CODES[401],
            message=error_reason(e),
            data=error_text(e),
        )
    except HTTPForbidden as e:
        return error_json_response(
            http_status=403,
            status=HTTP_ERROR_CODES[403],
            message=error_reason(e),
            data=error_text(e),
        )
    except HTTPNotFound as e:
        return error_json_response(
            http_status=404,
            status=HTTP_ERROR_CODES[404],
            message=error_reason(e),
            data=error_text(e),
        )
    except HTTPMethodNotAllowed as e:
        return error_json_response(
            http_status=405,
            status=HTTP_ERROR_CODES[405],
            message=error_reason(e),
            data=error_text(e),
        )
    except HTTPConflict as e:
        return error_json_response(
            http_status=409,
            status=HTTP_ERROR_CODES[409],
            message=error_reason(e),
            data=error_text(e),
        )
    except HTTPServerError as e:
        return error_json_response(
            http_status=500,
            status=HTTP_ERROR_CODES[500],
            message=error_reason(e),
            data=error_text(e),
        )
    except Exception as e:
        return error_json_response(
            http_status=500,
            status=HTTP_ERROR_CODES[500],
            message=error_reason(e),
            data=error_text(e),
        )


def setup_middlewares(app: "Application"):
    app.middlewares.append(error_handling_middleware)
    app.middlewares.append(validation_middleware)
