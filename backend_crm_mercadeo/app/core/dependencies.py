from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.shared.database.session import get_db

_bearer_scheme = HTTPBearer()


def _con_tz_utc(momento: datetime) -> datetime:
    # Oracle devuelve TIMESTAMP como datetime "naive" (sin tz); todo lo que
    # este backend escribe en esas columnas ya es UTC (datetime.now(timezone.utc)),
    # asi que se asume UTC si llega sin tz en vez de comparar naive vs aware.
    return momento if momento.tzinfo else momento.replace(tzinfo=timezone.utc)


def _decodificar(credentials: HTTPAuthorizationCredentials) -> dict:
    payload = decode_access_token(credentials.credentials)
    if payload is None or not payload.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido o expirado"
        )
    return payload


# Version liviana: solo valida que el token sea real y no haya expirado, sin
# exigir rol ni chequear si quedo desactualizado. La usa exclusivamente
# GET /auth/me (ver modules/auth/router.py) - ese endpoint es justo el que el
# frontend usa para preguntar "¿cual es mi estado actual?" (para decidir si
# mandar a /sin-rol, o para revisar si ya le asignaron rol despues de un
# rato sin tenerlo). Si aplicara las mismas reglas que get_current_username
# quedaria bloqueado por su propio chequeo justo cuando mas se necesita: la
# regla de "token viejo" de mas abajo se dispara tambien la PRIMERA vez que
# a alguien le asignan rol (fecha_actualizado del rol siempre queda despues
# del iat de un token emitido cuando todavia no tenia ninguno).
def get_username_liviano(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> str:
    return _decodificar(credentials)["sub"]


def get_current_username(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> str:
    payload = _decodificar(credentials)
    username: str = payload["sub"]

    # Import local para evitar que este modulo "core" dependa de un modulo de
    # feature en el import top-level.
    from app.modules.auth.repository import AuthRepository

    ultimo_cambio_rol = AuthRepository(db).fecha_ultimo_cambio_rol(username)

    # Sin ningun rol de CRM_MERCADEO asignado: se bloquea el acceso a CUALQUIER
    # endpoint (defensa en profundidad - el frontend tambien bloquea la
    # navegacion, pero esto no depende de que ese chequeo exista o funcione).
    # No es 401 (eso dispara el logout automatico del frontend, ver
    # httpInterceptor.ts): el usuario SI esta autenticado, solo le falta rol.
    if ultimo_cambio_rol is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu usuario no tiene un rol asignado en el CRM. Contacta al administrador del sistema.",
        )

    # Si a este usuario le cambiaron el rol despues de que se emitio este
    # token, el token queda con permisos desactualizados: se rechaza para
    # forzar un login nuevo.
    iat = payload.get("iat")
    if iat is not None:
        emitido_en = datetime.fromtimestamp(iat, tz=timezone.utc)
        if _con_tz_utc(ultimo_cambio_rol) > emitido_en:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tu rol en el CRM cambio. Vuelve a iniciar sesion.",
            )

    return username


def requiere_permiso(permiso: str):
    """Dependencia que exige el permiso "modulo:accion" (INTRANET_PERMISOS_APP)
    al usuario del token; 403 si no lo tiene. Uso:
    `dependencies=[Depends(requiere_permiso("mailerturbo:ver"))]`."""

    def _verificar(
        username: str = Depends(get_current_username),
        db: Session = Depends(get_db),
    ) -> str:
        from app.modules.auth.repository import AuthRepository

        repo = AuthRepository(db)
        usuario = repo.obtener_por_usuario(username)
        if usuario is None or permiso not in repo.obtener_permisos(usuario.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No tienes permiso para esta accion ({permiso}).",
            )
        return username

    return _verificar


__all__ = ["get_db", "get_current_username", "get_username_liviano", "requiere_permiso"]
