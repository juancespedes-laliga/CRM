"""Auditoria de titulares y beneficiarios (Plan Liga).

Traduce las filas que devuelve el repository (obtener_titular /
obtener_beneficiario, con claves en MAYUSCULA y fechas 'DD/MM/YYYY') a filas
de mercadeo_crm_auditoria: nombre, documento, estado legible, vigencia en
ese momento y la lista de campos antes -> despues.
"""

from datetime import date, datetime

from app.modules.administracion.auditoria.registro import RegistradorAuditoria, campo_cambiado

MODULO_TITULARES = "titulares"
MODULO_BENEFICIARIOS = "beneficiarios"

ESTADOS = {"A": "Activo", "I": "Inactivo"}

# Campos que se comparan para el "antes -> despues" (clave del repository -> etiqueta).
ETIQUETAS = {
    "TIPO_DOCUMENTO": "Tipo de documento",
    "DOCUMENTO": "Documento",
    "NOMBRE1": "Primer nombre",
    "NOMBRE2": "Segundo nombre",
    "APELLIDO1": "Primer apellido",
    "APELLIDO2": "Segundo apellido",
    "FECHA_NACIMIENTO": "Fecha de nacimiento",
    "SEXO": "Sexo",
    "CORREO": "Correo",
    "TELEFONO": "Teléfono",
    "DIRECCION": "Dirección",
    "CIUDAD": "Ciudad",
    "DEPARTAMENTO": "Departamento",
    "EMPRESA": "Empresa",
    "TIPO_PLAN": "Plan",
    "TIPO_AFILIADO": "Tipo de afiliado",
    "EPS": "EPS",
    "OTRAEPS": "Otra EPS",
    "PLAN_SALUD": "Plan de salud",
    "PLAN_NOMBRE": "Nombre del plan",
    "FECHA_INGRESO": "Fecha de ingreso",
    "FECHA_RENOVADO": "Fecha de renovación",
    "RENOVADO": "Renovado",
}


def nombre_completo(fila: dict | None) -> str:
    if not fila:
        return ""
    return " ".join(
        p.strip() for p in (fila.get("NOMBRE1"), fila.get("NOMBRE2"), fila.get("APELLIDO1"), fila.get("APELLIDO2"))
        if p and p.strip()
    )


def _fecha(valor) -> date | None:
    if valor is None or valor == "":
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    try:
        return datetime.strptime(str(valor), "%d/%m/%Y").date()
    except ValueError:
        return None


def estado(fila: dict | None) -> str | None:
    if not fila:
        return None
    return ESTADOS.get(fila.get("ESTADO"), fila.get("ESTADO"))


def diferencias(antes: dict | None, despues: dict | None) -> list[dict]:
    """Campos que cambiaron entre dos filas (sin ESTADO: va en estado_antes/despues)."""
    antes, despues = antes or {}, despues or {}
    cambios = []
    for clave, etiqueta in ETIQUETAS.items():
        a, d = antes.get(clave), despues.get(clave)
        if (a or None) != (d or None):
            cambios.append(campo_cambiado(clave, etiqueta, a, d))
    return cambios


class AuditoriaPlanLiga:
    def __init__(self, registrador: RegistradorAuditoria) -> None:
        self.registrador = registrador

    def fila(
        self,
        modulo: str,
        accion: str,
        actual: dict,
        *,
        anterior: dict | None = None,
        registro_id: int | None = None,
        titular_id: int | None = None,
        cambios: list[dict] | None = None,
        motivo: str | None = None,
        origen: str | None = None,
        estado_despues: str | None = None,
    ) -> dict:
        """Fila de auditoria a partir del estado actual (despues) y, si hay, el anterior."""
        if registro_id is None:
            registro_id = actual.get("ID_TITULAR") if modulo == MODULO_TITULARES else actual.get("ID")
        return self.registrador.fila(
            modulo=modulo,
            accion=accion,
            registro_id=int(registro_id),
            registro_nombre=nombre_completo(actual) or nombre_completo(anterior),
            documento=actual.get("DOCUMENTO") or (anterior or {}).get("DOCUMENTO"),
            titular_id=titular_id,
            estado_antes=estado(anterior),
            estado_despues=estado_despues or estado(actual),
            fecha_ingreso=_fecha(actual.get("FECHA_INGRESO")),
            renovado=actual.get("RENOVADO"),
            fecha_renovado=_fecha(actual.get("FECHA_RENOVADO")),
            motivo=motivo,
            cambios=cambios if cambios is not None else diferencias(anterior, actual),
            origen=origen,
        )

    def registrar(self, *args, **kwargs) -> None:
        self.registrador.registrar_varios([self.fila(*args, **kwargs)])

    def registrar_varios(self, filas: list[dict]) -> None:
        self.registrador.registrar_varios(filas)
