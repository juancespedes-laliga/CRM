"""Cliente HTTP del Web Service de MailerTurbo.

MailerTurbo expone UNA sola URL (settings.mailerturbo_url) y decide la operacion
por el campo "metodo" del body:

    {"ws_login": {"usuario", "clave", "llave"}, "metodo": "ObtenerListas", "data": {...}}

Todas las respuestas traen idmensaje / mensaje / codigomensaje / tipomensaje / data
(y a veces "explicacion"); tipomensaje == "Error" indica fallo aunque el HTTP sea 200.

Sesion: los metodos de datos (listas, contactos, campanas) se autentican SOLO con
ws_login en cada peticion. IniciarSesion es de un afiliado (usuario de la plataforma)
y devuelve un tokensesion con fechaexpiracion; ese token se guarda (memoria + archivo)
y se reutiliza hasta que vence, ver obtener_token_sesion.
"""

import json
import logging
import threading
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.core.config import BASE_DIR, settings

logger = logging.getLogger(__name__)

TIMEOUT_SEGUNDOS = 60
# MailerTurbo devuelve las fechas en hora de Colombia (UTC-5, sin horario de verano).
ZONA_COLOMBIA = timezone(timedelta(hours=-5))
# Margen para no usar un token que esta a punto de vencer.
MARGEN_VENCIMIENTO = timedelta(minutes=10)
ARCHIVO_SESION = BASE_DIR / ".mailerturbo_sesion.json"


class MailerTurboError(Exception):
    """Error devuelto por MailerTurbo (o de conexion). `detail` es apto para el usuario."""

    def __init__(self, detail: str, codigo: str | None = None) -> None:
        super().__init__(detail)
        self.detail = detail
        self.codigo = codigo


def configurado() -> bool:
    return bool(
        settings.mailerturbo_usuario
        and settings.mailerturbo_clave
        and settings.mailerturbo_llave
        and settings.mailerturbo_idempresa
    )


def llamar(metodo: str, data: dict[str, Any]) -> Any:
    """Ejecuta un metodo del Web Service y devuelve el campo `data` de la respuesta.
    Lanza MailerTurboError si MailerTurbo responde tipomensaje == 'Error'."""
    if not configurado():
        raise MailerTurboError(
            "MailerTurbo no esta configurado en el servidor (variables MAILERTURBO_* del .env)."
        )
    cuerpo = json.dumps(
        {
            "ws_login": {
                "usuario": settings.mailerturbo_usuario,
                "clave": settings.mailerturbo_clave,
                "llave": settings.mailerturbo_llave,
            },
            "metodo": metodo,
            "data": data,
        }
    ).encode("utf-8")
    peticion = urllib.request.Request(
        settings.mailerturbo_url,
        data=cuerpo,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(peticion, timeout=TIMEOUT_SEGUNDOS) as respuesta:
            texto = respuesta.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError) as exc:
        logger.warning("MailerTurbo %s: error de conexion: %s", metodo, exc)
        raise MailerTurboError("No se pudo conectar con MailerTurbo.") from exc

    try:
        resultado = json.loads(texto)
    except json.JSONDecodeError as exc:
        logger.warning("MailerTurbo %s: respuesta no JSON: %s", metodo, texto[:300])
        raise MailerTurboError("MailerTurbo devolvio una respuesta inesperada.") from exc

    if resultado.get("tipomensaje") == "Error":
        mensaje = resultado.get("mensaje") or "Error de MailerTurbo"
        explicacion = resultado.get("explicacion")
        detalle = f"{mensaje}: {explicacion}" if explicacion else mensaje
        raise MailerTurboError(detalle, resultado.get("codigomensaje"))
    return resultado.get("data")


# ── Sesion de afiliado (token reutilizable hasta que vence) ─────────────
_lock_sesion = threading.Lock()
_sesion: dict[str, Any] = {}


def _ahora() -> datetime:
    return datetime.now(ZONA_COLOMBIA)


def _vigente(sesion: dict[str, Any]) -> bool:
    try:
        expira = datetime.strptime(sesion["fechaexpiracion"], "%Y-%m-%d %H:%M:%S")
    except (KeyError, TypeError, ValueError):
        return False
    return bool(sesion.get("tokensesion")) and expira.replace(
        tzinfo=ZONA_COLOMBIA
    ) - MARGEN_VENCIMIENTO > _ahora()


def _leer_archivo() -> dict[str, Any]:
    try:
        return json.loads(Path(ARCHIVO_SESION).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _guardar_archivo(sesion: dict[str, Any]) -> None:
    try:
        Path(ARCHIVO_SESION).write_text(json.dumps(sesion), encoding="utf-8")
    except OSError as exc:  # sin permisos de escritura: queda solo en memoria
        logger.warning("No se pudo guardar la sesion de MailerTurbo: %s", exc)


def obtener_token_sesion(forzar_nueva: bool = False) -> dict[str, Any]:
    """Devuelve {"tokensesion", "fechaexpiracion"} de la sesion del afiliado.

    Reutiliza el token guardado (memoria y, tras un reinicio, el archivo) mientras
    no haya vencido; si vencio o no hay, hace IniciarSesion y guarda el nuevo."""
    if not (settings.mailerturbo_afiliado_nick and settings.mailerturbo_afiliado_clave):
        raise MailerTurboError(
            "Falta configurar el usuario de MailerTurbo (MAILERTURBO_AFILIADO_NICK/CLAVE)."
        )
    with _lock_sesion:
        if not forzar_nueva:
            if not _sesion:
                _sesion.update(_leer_archivo())
            if _vigente(_sesion):
                return dict(_sesion)

        data = llamar(
            "IniciarSesion",
            {
                "nick": settings.mailerturbo_afiliado_nick,
                "clave": settings.mailerturbo_afiliado_clave,
                "tipoapp": "Web",
            },
        )
        if not isinstance(data, dict) or not data.get("tokensesion"):
            raise MailerTurboError("MailerTurbo no devolvio un token de sesion.")
        _sesion.clear()
        _sesion.update(
            {
                "tokensesion": data["tokensesion"],
                "fechaexpiracion": data.get("fechaexpiracion"),
            }
        )
        _guardar_archivo(_sesion)
        logger.info("MailerTurbo: nueva sesion, vence %s", _sesion["fechaexpiracion"])
        return dict(_sesion)


def invalidar_sesion() -> None:
    with _lock_sesion:
        _sesion.clear()
        try:
            Path(ARCHIVO_SESION).unlink(missing_ok=True)
        except OSError:
            pass
