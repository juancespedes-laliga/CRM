"""
Usa OAuth2 (Gmail API): el refresh_token 

"""

import base64
import json
import logging
import threading
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import BASE_DIR, settings

logger = logging.getLogger(__name__)

# app/templates/emails/ - ahi van los .html (Jinja2) que arma enviar_correo_plantilla.
TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates" / "emails"

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
TOKEN_URI = "https://oauth2.googleapis.com/token"

_jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html"]),
)


def _verificar_configurado() -> None:
    faltantes = [
        nombre
        for nombre, valor in [
            ("GMAIL_SENDER_EMAIL", settings.gmail_sender_email),
            ("GMAIL_OAUTH_CLIENT_ID", settings.gmail_oauth_client_id),
            ("GMAIL_OAUTH_CLIENT_SECRET", settings.gmail_oauth_client_secret),
            ("GMAIL_OAUTH_REFRESH_TOKEN", settings.gmail_oauth_refresh_token),
        ]
        if not valor
    ]
    if faltantes:
        raise RuntimeError(f"Falta configurar en .env: {', '.join(faltantes)}")


def _servicio_gmail():
    # token=None a proposito: no guardamos access_token (dura ~1h), la libreria de
    # Google lo saca solo del refresh_token en cada llamada.
    credenciales = Credentials(
        token=None,
        refresh_token=settings.gmail_oauth_refresh_token,
        client_id=settings.gmail_oauth_client_id,
        client_secret=settings.gmail_oauth_client_secret,
        token_uri=TOKEN_URI,
        scopes=SCOPES,
    )
    return build("gmail", "v1", credentials=credenciales)


def _armar_mensaje_crudo(destinatarios: list[str], asunto: str, cuerpo_html: str) -> dict:
    mensaje = MIMEText(cuerpo_html, "html", "utf-8")
    mensaje["to"] = ", ".join(destinatarios)
    mensaje["from"] = settings.gmail_sender_email
    mensaje["subject"] = asunto
    crudo = base64.urlsafe_b64encode(mensaje.as_bytes()).decode("utf-8")
    return {"raw": crudo}


# ── Tope diario de envios (settings.gmail_limite_diario) ────────────────
# Gmail bloquea la cuenta si manda demasiados correos en un dia. Todo envio del
# CRM pasa por enviar_correo, asi que aqui se cuenta (por destinatario) y se
# corta al llegar al tope. El conteo se guarda en un archivo para que sobreviva
# a un reinicio del backend.
ZONA_COLOMBIA = timezone(timedelta(hours=-5))
ARCHIVO_CONTEO = BASE_DIR / ".gmail_envios_dia.json"
_lock_conteo = threading.Lock()


class LimiteDiarioCorreosError(RuntimeError):
    """Se alcanzo (o se pasaria) el tope diario de correos por Gmail."""


def _hoy() -> str:
    return datetime.now(ZONA_COLOMBIA).strftime("%Y-%m-%d")


def _leer_conteo() -> int:
    try:
        datos = json.loads(Path(ARCHIVO_CONTEO).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return 0
    return int(datos.get("enviados", 0)) if datos.get("fecha") == _hoy() else 0


def _guardar_conteo(enviados: int) -> None:
    try:
        Path(ARCHIVO_CONTEO).write_text(
            json.dumps({"fecha": _hoy(), "enviados": enviados}), encoding="utf-8"
        )
    except OSError as exc:
        logger.warning("No se pudo guardar el conteo de correos del dia: %s", exc)


def uso_diario() -> dict:
    """{"fecha", "enviados", "limite", "disponibles"}; limite/disponibles None si no hay tope."""
    with _lock_conteo:
        enviados = _leer_conteo()
    limite = settings.gmail_limite_diario or None
    return {
        "fecha": _hoy(),
        "enviados": enviados,
        "limite": limite,
        "disponibles": max(0, limite - enviados) if limite else None,
    }


def verificar_cupo(cantidad: int) -> None:
    """Lanza LimiteDiarioCorreosError si `cantidad` correos no caben en el cupo de hoy.
    Los envios masivos la llaman ANTES de empezar, para no quedar a medias."""
    uso = uso_diario()
    if uso["limite"] is not None and cantidad > uso["disponibles"]:
        raise LimiteDiarioCorreosError(
            f"Se pasaría el límite diario de correos por Gmail: hoy quedan "
            f"{uso['disponibles']} de {uso['limite']} y este envío necesita {cantidad}. "
            "Envíelo mañana o use MailerTurbo para envíos masivos."
        )


def enviar_correo(destinatarios: list[str], asunto: str, cuerpo_html: str) -> None:
    """Manda un HTML ya armado (sin plantilla) a la lista de destinatarios.
    Respeta el tope diario: lanza LimiteDiarioCorreosError si no hay cupo."""
    _verificar_configurado()
    # El lock cubre revisar + enviar + contar, para que dos envios a la vez no
    # se pasen del tope entre los dos.
    with _lock_conteo:
        enviados = _leer_conteo()
        limite = settings.gmail_limite_diario
        if limite and enviados + len(destinatarios) > limite:
            raise LimiteDiarioCorreosError(
                f"Se alcanzó el límite diario de {limite} correos por Gmail. "
                "Se podrá enviar de nuevo mañana."
            )
        servicio = _servicio_gmail()
        cuerpo = _armar_mensaje_crudo(destinatarios, asunto, cuerpo_html)
        servicio.users().messages().send(userId="me", body=cuerpo).execute()
        _guardar_conteo(enviados + len(destinatarios))


def enviar_correo_plantilla(
    destinatarios: list[str], asunto: str, plantilla: str, variables: dict
) -> None:
    """Renderiza app/templates/emails/<plantilla> (Jinja2) con `variables` y lo manda.
    `plantilla` es el nombre del archivo, ej. "Bienvenida (1).html"."""
    cuerpo_html = _jinja_env.get_template(plantilla).render(**variables)
    enviar_correo(destinatarios, asunto, cuerpo_html)
