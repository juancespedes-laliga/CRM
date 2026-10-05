import logging

import oracledb
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError

logger = logging.getLogger(__name__)


class NotFoundError(Exception):
    def __init__(self, detail: str = "Recurso no encontrado") -> None:
        self.detail = detail


class ConflictError(Exception):
    def __init__(self, detail: str = "El recurso ya existe o entra en conflicto") -> None:
        self.detail = detail


class UnauthorizedError(Exception):
    def __init__(self, detail: str = "No autorizado") -> None:
        self.detail = detail


class ForbiddenError(Exception):
    def __init__(self, detail: str = "Acceso denegado") -> None:
        self.detail = detail


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundError)
    async def not_found_handler(_: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": exc.detail})

    @app.exception_handler(ConflictError)
    async def conflict_handler(_: Request, exc: ConflictError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": exc.detail})

    @app.exception_handler(UnauthorizedError)
    async def unauthorized_handler(_: Request, exc: UnauthorizedError) -> JSONResponse:
        return JSONResponse(status_code=401, content={"detail": exc.detail})

    @app.exception_handler(ForbiddenError)
    async def forbidden_handler(_: Request, exc: ForbiddenError) -> JSONResponse:
        return JSONResponse(status_code=403, content={"detail": exc.detail})

    @app.exception_handler(oracledb.IntegrityError)
    async def oracle_integrity_handler(_: Request, exc: oracledb.IntegrityError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": _mensaje_integridad(str(exc))})

    @app.exception_handler(oracledb.Error)
    async def oracle_error_handler(request: Request, exc: oracledb.Error) -> JSONResponse:
        # Se registra el error completo (con su codigo ORA-) porque al usuario solo le
        # llega un mensaje generico y sin esto no queda rastro en la consola del backend.
        logger.exception("Error de Oracle en %s", request.url.path)
        return JSONResponse(status_code=503, content={"detail": _mensaje_oracle(str(exc))})

    # SQLAlchemy envuelve los errores del driver oracledb en sus propias clases
    # (sqlalchemy.exc.*), por lo que los handlers de oracledb.Error/IntegrityError
    # de arriba nunca se disparan cuando el error viene de una consulta ORM: sin
    # este handler, la excepcion queda sin capturar, se pierde la respuesta antes
    # de llegar al CORSMiddleware y el navegador reporta un falso error de CORS.
    @app.exception_handler(DBAPIError)
    async def sqlalchemy_dbapi_error_handler(request: Request, exc: DBAPIError) -> JSONResponse:
        mensaje = str(exc.orig) if exc.orig is not None else str(exc)
        logger.exception("Error de base de datos en %s", request.url.path)
        if exc.__class__.__name__ == "IntegrityError":
            return JSONResponse(status_code=400, content={"detail": _mensaje_integridad(mensaje)})
        return JSONResponse(status_code=503, content={"detail": _mensaje_oracle(mensaje)})

    # Red de seguridad: cualquier otra excepcion no capturada tambien debe pasar
    # por aqui para que la respuesta conserve las cabeceras CORS.
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Error no controlado en %s", request.url.path)
        return JSONResponse(
            status_code=500, content={"detail": "Error interno del servidor. Intente de nuevo."}
        )


def _mensaje_integridad(mensaje: str) -> str:
    if "ORA-00001" in mensaje:
        return "Ya existe un registro duplicado con esos datos."
    if "ORA-01400" in mensaje:
        return "Faltan datos obligatorios."
    return "No se pudo completar la operacion en la base de datos."


def _mensaje_oracle(mensaje: str) -> str:
    if "ORA-28001" in mensaje:
        return "La contraseña de la base de datos ha expirado. Contacte al administrador del sistema."
    if "ORA-01017" in mensaje:
        return "Usuario o contraseña de la base de datos incorrectos. Contacte al administrador del sistema."
    if "ORA-12170" in mensaje or "TNS" in mensaje.upper():
        return "No se pudo conectar con Oracle (tiempo de espera agotado). Verifique red/VPN e intente de nuevo."
    return "Error de base de datos. Intente de nuevo en unos segundos."
