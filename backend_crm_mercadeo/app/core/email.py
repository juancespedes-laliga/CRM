"""
Usa OAuth2 (Gmail API): el refresh_token 

"""

import base64
from email.mime.text import MIMEText
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import settings

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


def enviar_correo(destinatarios: list[str], asunto: str, cuerpo_html: str) -> None:
    """Manda un HTML ya armado (sin plantilla) a la lista de destinatarios."""
    _verificar_configurado()
    servicio = _servicio_gmail()
    cuerpo = _armar_mensaje_crudo(destinatarios, asunto, cuerpo_html)
    servicio.users().messages().send(userId="me", body=cuerpo).execute()


def enviar_correo_plantilla(
    destinatarios: list[str], asunto: str, plantilla: str, variables: dict
) -> None:
    """Renderiza app/templates/emails/<plantilla> (Jinja2) con `variables` y lo manda.
    `plantilla` es el nombre del archivo, ej. "Bienvenida (1).html"."""
    cuerpo_html = _jinja_env.get_template(plantilla).render(**variables)
    enviar_correo(destinatarios, asunto, cuerpo_html)
