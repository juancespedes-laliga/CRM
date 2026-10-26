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
import re
import threading
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

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


def ejecutar(metodo: str, data: dict[str, Any]) -> dict[str, Any]:
    """Ejecuta un metodo y devuelve la respuesta completa (data, explicacion, etc.).
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
    return resultado


def llamar(metodo: str, data: dict[str, Any]) -> Any:
    """Ejecuta un metodo del Web Service y devuelve solo el campo `data`."""
    return ejecutar(metodo, data).get("data")


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


# ── Editor de la campaña (sencillo = TinyMCE, plus = Topol) ──────────
# El plus es el mismo "E-mail editor" que MailerTurbo abre en Diseñar mi mensaje.
# La clave vive en el HTML del panel (no en el Web Service); se lee con la sesión
# del afiliado y solo se entrega a quien ya puede enviar campañas.
_PANEL = "https://mailerturbo.com"
_RE_API_TOPOL = re.compile(r'id="topol_api_token"\s+value="([^"]+)"')
_RE_USER_TOPOL = re.compile(r'id="topol_user_id"\s+value="([^"]+)"')
_cache_editor: dict[str, Any] = {}
_cache_editor_hasta: datetime | None = None
_lock_editor = threading.Lock()


def _panel_autenticado() -> urllib.request.OpenerDirector:
    token = obtener_token_sesion()["tokensesion"]
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
    peticion = urllib.request.Request(
        f"{_PANEL}/iniciar-sesion",
        data=urlencode({"tokensesion": token}).encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with opener.open(peticion, timeout=TIMEOUT_SEGUNDOS) as respuesta:
            respuesta.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise MailerTurboError("No se pudo abrir la sesión del editor de MailerTurbo.") from exc
    return opener


def _panel_texto(opener: urllib.request.OpenerDirector, url: str, data: dict[str, str] | None = None) -> str:
    cuerpo = urlencode(data).encode() if data is not None else None
    peticion = urllib.request.Request(
        url,
        data=cuerpo,
        headers={"Content-Type": "application/x-www-form-urlencoded"} if cuerpo else {},
        method="POST" if cuerpo is not None else "GET",
    )
    try:
        with opener.open(peticion, timeout=TIMEOUT_SEGUNDOS) as respuesta:
            return respuesta.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError) as exc:
        raise MailerTurboError("No se pudo consultar el editor de MailerTurbo.") from exc


def configuracion_editor_plus() -> dict[str, Any]:
    """Clave del editor plus, tags {{NAME}}… y plantillas guardadas en MailerTurbo."""
    global _cache_editor_hasta
    with _lock_editor:
        if _cache_editor and _cache_editor_hasta and _cache_editor_hasta > _ahora():
            return dict(_cache_editor)

    opener = _panel_autenticado()
    html = _panel_texto(opener, f"{_PANEL}/af-templates")
    api = _RE_API_TOPOL.search(html)
    user = _RE_USER_TOPOL.search(html)
    if not api or not user:
        raise MailerTurboError("MailerTurbo no mostró la clave del editor plus.")

    try:
        tags_raw = json.loads(_panel_texto(opener, f"{_PANEL}/af-campaign", {"op": "getTags", "noheaders": "all"}))
        if isinstance(tags_raw, str):
            tags_raw = json.loads(tags_raw)
        plantillas_raw = json.loads(
            _panel_texto(opener, f"{_PANEL}/af-campaign", {"op": "obtenerPlantillasTopol", "noheaders": "all"})
        )
    except json.JSONDecodeError as exc:
        raise MailerTurboError("MailerTurbo devolvió el editor en un formato inesperado.") from exc
    tags = [
        {"grupo": str(t.get("group") or "Otros"), "tag": str(t.get("tag") or "")}
        for t in (tags_raw if isinstance(tags_raw, list) else [])
        if isinstance(t, dict) and t.get("tag")
    ]

    plantillas = []
    for p in plantillas_raw if isinstance(plantillas_raw, list) else []:
        if not isinstance(p, dict):
            continue
        info = p.get("infotopol")
        if isinstance(info, (dict, list)):
            info = json.dumps(info)
        plantillas.append(
            {
                "id": int(p.get("idtemplate") or 0),
                "nombre": p.get("nombretemplate") or "",
                "documento": info or "",
            }
        )

    datos = {"api_key": api.group(1), "user_id": user.group(1), "tags": tags, "plantillas": plantillas}
    with _lock_editor:
        _cache_editor.clear()
        _cache_editor.update(datos)
        _cache_editor_hasta = _ahora() + timedelta(minutes=10)
    return dict(datos)


def subir_imagen_editor(nombre: str, contenido: bytes, content_type: str) -> str:
    """Sube una imagen al archivo de MailerTurbo y devuelve la URL pública (la usa el editor plus)."""
    opener = _panel_autenticado()
    limite = 8 * 1024 * 1024
    if len(contenido) > limite:
        raise MailerTurboError("La imagen supera 8 MB.")
    nombre_limpio = Path(nombre or "imagen").name.replace('"', "") or "imagen"
    tipo = content_type if content_type and content_type.startswith("image/") else "application/octet-stream"
    boundary = f"----crm{uuid.uuid4().hex}"
    cuerpo = b"".join(
        [
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="file"; filename="{nombre_limpio}"\r\n'.encode(),
            f"Content-Type: {tipo}\r\n\r\n".encode(),
            contenido,
            f"\r\n--{boundary}--\r\n".encode(),
        ]
    )
    peticion = urllib.request.Request(
        f"{_PANEL}/af-templates?op=uploadImageTopol&noheaders=all",
        data=cuerpo,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    try:
        with opener.open(peticion, timeout=TIMEOUT_SEGUNDOS) as respuesta:
            texto = respuesta.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError) as exc:
        raise MailerTurboError("No se pudo subir la imagen a MailerTurbo.") from exc
    try:
        data = json.loads(texto)
    except json.JSONDecodeError as exc:
        raise MailerTurboError("MailerTurbo no confirmó la imagen.") from exc
    if data.get("respuesta") != "ok" or not data.get("url"):
        raise MailerTurboError(data.get("mensaje") or data.get("error") or "No se pudo subir la imagen.")
    return str(data["url"])
