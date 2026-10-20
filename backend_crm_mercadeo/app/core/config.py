from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Backend CRM Mercadeo"
    api_prefix: str = "/api"

    # Sin default: debe venir de .env / variables de entorno. Tiene que ser
    # identico al SECRET_KEY del backend Login/SSO (firma los mismos tokens
    # JWT que este backend valida) - un default aqui esconderia el error si
    # algun ambiente se queda sin configurar, en vez de fallar al arrancar.
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480

    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://160.2.1.80:3000",
        "http://160.2.1.80:5175",
        # Producción vía Traefik (TLS termina en el proxy; same-origin con el frontend).
        "https://crm.laliga.org.co",
        # Acceso directo por IP/puerto (depuración sin Traefik).
        "http://160.2.1.22:8090",
        "http://160.2.1.22:8100",
        "http://localhost:8090",
        "http://127.0.0.1:8090",
    ]

    scse_db_user: str = ""
    scse_db_passwd: str = ""
    scse_db_ip: str = "localhost"
    scse_db_port: int = 1521
    scse_db_database: str = ""

    # Envio de correo (campañas/automatizaciones). Con Gmail: smtp_user es la cuenta
    # completa (ej. "algo@gmail.com") y smtp_password es una "contraseña de aplicacion"
    # de 16 caracteres (myaccount.google.com/security -> Verificacion en dos pasos ->
    # Contraseñas de aplicaciones), NUNCA la contraseña normal de la cuenta.
    # Vacio por defecto (como scse_db_*): el backend arranca igual sin esto configurado,
    # solo falla al intentar mandar un correo.
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_name: str = "CRM Mercadeo LaLiga"

    # Envio de correo via Gmail API (OAuth2) - reemplaza el SMTP de arriba. El
    # refresh_token se obtiene una sola vez con scripts/obtener_refresh_token_gmail.py.
    gmail_sender_email: str = ""
    gmail_oauth_client_id: str = ""
    gmail_oauth_client_secret: str = ""
    gmail_oauth_refresh_token: str = ""

    # MailerTurbo (correo masivo). Cada peticion del Web Service se autentica con
    # usuario/clave/llave (ws_login); idempresa es la empresa de LaLiga en la plataforma.
    # afiliado_nick/clave son de un USUARIO de la plataforma (opcional): solo se usan
    # para IniciarSesion, que da un token para abrir MailerTurbo ya logueado.
    mailerturbo_url: str = "https://mailerturbo.com/apiserver"
    mailerturbo_usuario: str = ""
    mailerturbo_clave: str = ""
    mailerturbo_llave: str = ""
    mailerturbo_idempresa: int = 0
    mailerturbo_afiliado_nick: str = ""
    mailerturbo_afiliado_clave: str = ""
    # Correos que permite el plan de MailerTurbo por mes (0 = sin configurar).
    mailerturbo_limite_mensual: int = 0

    @property
    def database_url(self) -> str:
        return (
            f"oracle+oracledb://{self.scse_db_user}:{self.scse_db_passwd}"
            f"@{self.scse_db_ip}:{self.scse_db_port}/?service_name={self.scse_db_database}"
        )


settings = Settings()
