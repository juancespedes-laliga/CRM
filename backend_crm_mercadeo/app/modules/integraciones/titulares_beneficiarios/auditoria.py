"""Auditoria de titulares y beneficiarios (Plan Liga).

Traduce las filas que devuelve el repository (obtener_titular /
obtener_beneficiario, con claves en MAYUSCULA y fechas 'DD/MM/YYYY') a filas
de mercadeo_crm_auditoria.

fecha_inscripcion solo se llena en accion 'creacion' (alta de alguien que no
existia). En el resto de eventos queda NULL.
estado_antes / estado_despues se guardan como A / I.
"""

from datetime import date, datetime

from app.modules.administracion.auditoria.registro import RegistradorAuditoria, campo_cambiado

MODULO_TITULARES = "titulares"
MODULO_BENEFICIARIOS = "beneficiarios"

# Campos que se comparan para el "antes -> despues" (clave del repository -> etiqueta).
# Ya no se persisten en la tabla (se quito CAMBIOS); se mantienen por si un
# llamador local quiere listar diferencias.
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
    texto = str(valor).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(texto[:10], fmt).date()
        except ValueError:
            continue
    return None


def estado(fila: dict | None) -> str | None:
    """Estado crudo A/I (como en intranet_planliga)."""
    if not fila:
        return None
    valor = fila.get("ESTADO")
    return str(valor).strip().upper()[:1] if valor else None


def diferencias(antes: dict | None, despues: dict | None) -> list[dict]:
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
        registro_id = int(registro_id)

        if modulo == MODULO_TITULARES:
            id_titular = registro_id
            id_beneficiario = None
        else:
            id_beneficiario = registro_id
            id_titular = int(titular_id) if titular_id is not None else (
                int(actual["ID_TITULAR"]) if actual.get("ID_TITULAR") is not None else None
            )

        # Solo en alta nueva: no se reescribe en renovacion/edicion/activacion.
        fecha_inscripcion = None
        if accion == "creacion":
            fecha_inscripcion = (
                _fecha(actual.get("FECHA_INSCRIPCION"))
                or _fecha(actual.get("FECHA_INGRESO"))
            )

        # motivo/cambios ya no se guardan en la tabla; se aceptan por compatibilidad
        # de firmas de los callers existentes.
        _ = (cambios, motivo)

        return self.registrador.fila(
            modulo=modulo,
            accion=accion,
            registro_nombre=nombre_completo(actual) or nombre_completo(anterior),
            documento=actual.get("DOCUMENTO") or (anterior or {}).get("DOCUMENTO"),
            id_titular=id_titular,
            id_beneficiario=id_beneficiario,
            estado_antes=estado(anterior),
            estado_despues=(estado_despues or estado(actual)),
            fecha_inscripcion=fecha_inscripcion,
            fecha_registro=_fecha(actual.get("FECHA_REGISTRO")),
            fecha_ingreso=_fecha(actual.get("FECHA_INGRESO")),
            renovado=actual.get("RENOVADO"),
            origen=origen,
        )

    def registrar(self, *args, **kwargs) -> None:
        self.registrador.registrar_varios([self.fila(*args, **kwargs)])

    def registrar_varios(self, filas: list[dict]) -> None:
        self.registrador.registrar_varios(filas)
