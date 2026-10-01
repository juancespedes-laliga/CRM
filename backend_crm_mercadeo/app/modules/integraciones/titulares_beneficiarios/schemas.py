import re
from datetime import date
from typing import Any, Optional

from pydantic import BaseModel, field_validator, model_validator

_PATRON_COLOR_HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")


class EntradaMayusculas(BaseModel):
    """Base para los esquemas que reciben datos del cliente: normaliza a
    mayusculas cualquier valor de texto, sin importar como lo haya escrito
    el usuario (minusculas, mixto, etc.), para mantener consistencia con los
    datos legacy en Oracle."""

    @model_validator(mode="before")
    @classmethod
    def normalizar_mayusculas(cls, datos: Any) -> Any:
        if not isinstance(datos, dict):
            return datos
        return {
            campo: valor.upper() if isinstance(valor, str) else valor
            for campo, valor in datos.items()
        }


class ResumenTitularesBeneficiarios(BaseModel):
    titulares_activos: int
    beneficiarios_activos: int


class PlanItem(BaseModel):
    ID: int
    NOMBRE: str
    TIPO: Optional[str] = None
    MAX_BENEFICIARIOS: Optional[int] = None
    BENEFICIARIOS_ADICIONALES: Optional[int] = None
    DESCRIPCION: Optional[str] = None
    ESTADO: Optional[str] = None


class PlanNombre(BaseModel):
    ID: int
    NOMBRE: str


class TitularDetalle(BaseModel):
    ID_TITULAR: int
    DOCUMENTO: Optional[str] = None
    TIPO_DOCUMENTO: Optional[str] = None
    NOMBRE1: Optional[str] = None
    NOMBRE2: Optional[str] = None
    APELLIDO1: Optional[str] = None
    APELLIDO2: Optional[str] = None
    FECHA_NACIMIENTO: Optional[str] = None
    SEXO: Optional[str] = None
    CORREO: Optional[str] = None
    TELEFONO: Optional[str] = None
    DIRECCION: Optional[str] = None
    CIUDAD: Optional[str] = None
    DEPARTAMENTO: Optional[str] = None
    TIPO_PLAN: Optional[str] = None
    TIPO_PLAN_ID: Optional[int] = None
    TIPO_AFILIADO: Optional[str] = None
    EMPRESA: Optional[str] = None
    EPS: Optional[str] = None
    OTRAEPS: Optional[str] = None
    PLAN_SALUD: Optional[str] = None
    PLAN_NOMBRE: Optional[str] = None
    ESTADO: Optional[str] = None
    FECHA_INGRESO: Optional[str] = None


class ListadoTitulares(BaseModel):
    ID_TITULAR: int
    TITULAR: str
    EMAIL: Optional[str] = None
    TELEFONO: Optional[str] = None
    TIPO_DOCUMENTO: Optional[str] = None
    DOCUMENTO: str
    EMPRESA: Optional[str] = None
    PLANES: Optional[str] = None
    # Tipo de plan crudo (INTRANET_PLANLIGA.TIPO_PLAN), distinto de PLANES (el
    # nombre del catalogo PlanLigaTipoPlan): se muestra en su propia columna
    # "Tipo de Plan" en la tabla, separada de "Plan Contratado".
    TIPO_PLAN: Optional[str] = None
    BENEFICIARIOS: Optional[str] = None
    INSCRIPCION: Optional[str] = None
    ESTADO: str


class TitularUpdate(EntradaMayusculas):
    DOCUMENTO: Optional[str] = None
    TIPO_DOCUMENTO: Optional[str] = None
    NOMBRE1: Optional[str] = None
    NOMBRE2: Optional[str] = None
    APELLIDO1: Optional[str] = None
    APELLIDO2: Optional[str] = None
    FECHA_NACIMIENTO: Optional[date] = None
    SEXO: Optional[str] = None
    CORREO: Optional[str] = None
    TELEFONO: Optional[str] = None
    DIRECCION: Optional[str] = None
    CIUDAD: Optional[str] = None
    DEPARTAMENTO: Optional[str] = None
    EMPRESA: Optional[str] = None
    ESTADO: Optional[str] = None
    # Cambio del "Plan Contratado" (TIPO_PLAN_ID del catalogo) al editar. Mismo
    # patron que TitularActivar: CAMBIAR_PLAN es un toggle explicito porque
    # None (Plan Estandar) es una eleccion valida en si misma, no "no toques el
    # plan". El backend revalida el permiso planliga:elegir_plan (ver
    # PERMISO_ELEGIR_PLAN en service.py); si el usuario no lo tiene,
    # CAMBIAR_PLAN se ignora aunque venga en True.
    CAMBIAR_PLAN: bool = False
    TIPO_PLAN_ID: Optional[int] = None


class TitularActivar(BaseModel):
    FECHA_INGRESO: date
    # Si es True (default, el comportamiento de siempre), la fecha tambien se
    # aplica a los beneficiarios activos de este titular. En False, solo
    # cambia la fecha del titular.
    APLICAR_A_GRUPO: bool = True
    # Permite cambiar el plan del titular al renovar (ej. de Estandar a uno
    # superior). CAMBIAR_PLAN es un toggle explicito -no basta con mandar
    # TIPO_PLAN_ID- porque None es una eleccion valida en si misma (Plan
    # Estandar): sin el toggle no habria forma de distinguir "no toques el
    # plan" de "cambialo a Estandar". El backend igual revalida el permiso
    # planliga:elegir_plan (ver PERMISO_ELEGIR_PLAN en service.py); si el
    # usuario no lo tiene, CAMBIAR_PLAN se ignora aunque venga en True.
    CAMBIAR_PLAN: bool = False
    TIPO_PLAN: Optional[str] = None
    TIPO_PLAN_ID: Optional[int] = None


class CambioFechaIngresoGrupo(BaseModel):
    """El grupo se define por EMPRESA o por TIPO_PLAN (uno de los dos, no
    ambos): ver PlanLiga.empresa / PlanLiga.tipo_plan. Coincidencia exacta en
    los dos casos, no LIKE -- el valor viene de un selector (catalogo de
    Empresas o de GET /grupo/tipos-plan), no de texto libre."""

    EMPRESA: Optional[str] = None
    TIPO_PLAN: Optional[str] = None
    FECHA_INGRESO: date

    @model_validator(mode="after")
    def _validar_un_solo_criterio(self) -> "CambioFechaIngresoGrupo":
        if bool(self.EMPRESA) == bool(self.TIPO_PLAN):
            raise ValueError(
                "Indique EMPRESA o TIPO_PLAN (exactamente uno de los dos)"
            )
        return self


class CambioFechaIngresoGrupoResultado(BaseModel):
    titulares_actualizados: int
    beneficiarios_actualizados: int


class TipoPlanValores(BaseModel):
    """GET /grupo/tipos-plan: valores distintos de INTRANET_PLANLIGA.TIPO_PLAN,
    para el selector de 'Cambiar fecha de ingreso por grupo'."""

    valores: list[str]


class ReemplazoPersona(EntradaMayusculas):
    """Datos de la persona nueva que reemplaza al titular/beneficiario actual.
    El plan, cupo y demas datos legacy (tipo_plan, eps, plan_salud, etc.) se
    heredan del registro reemplazado, no se piden aqui."""

    TIPO_DOCUMENTO: str
    DOCUMENTO: str
    NOMBRE1: str
    NOMBRE2: Optional[str] = None
    APELLIDO1: str
    APELLIDO2: Optional[str] = None
    FECHA_NACIMIENTO: Optional[date] = None
    SEXO: Optional[str] = None
    DIRECCION: Optional[str] = None
    CIUDAD: Optional[str] = None
    DEPARTAMENTO: Optional[str] = None
    CORREO: Optional[str] = None
    TELEFONO: Optional[str] = None
    EMPRESA: Optional[str] = None


class ReemplazoTitularResultado(BaseModel):
    titular_anterior_id: int
    titular_nuevo: TitularDetalle
    beneficiarios_reasignados: int
    usuario_servinte_creado: bool
    marcado_en_incle: bool
    registros_incle_marcados_anterior: int


class TitularCrear(EntradaMayusculas):
    TIPO_PLAN: Optional[str] = None
    TIPO_DOCUMENTO: str
    DOCUMENTO: str
    NOMBRE1: str
    NOMBRE2: Optional[str] = None
    APELLIDO1: str
    APELLIDO2: Optional[str] = None
    FECHA_NACIMIENTO: Optional[date] = None
    SEXO: Optional[str] = None
    DIRECCION: Optional[str] = None
    CIUDAD: Optional[str] = None
    DEPARTAMENTO: Optional[str] = None
    CORREO: Optional[str] = None
    TELEFONO: Optional[str] = None
    FECHA_INGRESO: date
    TIPO_AFILIADO: str
    EMPRESA: Optional[str] = None
    EPS: Optional[str] = None
    OTRAEPS: Optional[str] = None
    PLAN_SALUD: str
    PLAN_NOMBRE: Optional[str] = None
    TIPO_PLAN_ID: Optional[int] = None
    FACTURA: Optional[str] = None
    # False solo desde la carga masiva por Excel (ver frontend: cargaMasiva.ts): un alta
    # manual individual si manda el correo de registro, una importacion de muchos no.
    ENVIAR_CORREO_REGISTRO: bool = True


class CreacionTitularResultado(BaseModel):
    titular: TitularDetalle
    usuario_servinte_creado: bool
    marcado_en_incle: bool


class ActivacionTitularResultado(BaseModel):
    titular: TitularDetalle
    beneficiarios_activados: int
    registros_incle_desmarcados: int


class DesactivacionTitularResultado(BaseModel):
    titular: TitularDetalle
    beneficiarios_desactivados: int
    registros_incle_marcados: int


class ListadoTitularesPaginado(BaseModel):
    items: list[ListadoTitulares]
    total: int
    limit: int
    offset: int


class RenovacionMesItem(BaseModel):
    """Una fila de GET /titulares-beneficiarios/renovaciones: un titular cuyo
    FECHA_INGRESO cae en el mes consultado (se activo o reactivo ese mes)."""

    ID: int
    TIPO_DOCUMENTO: Optional[str] = None
    DOCUMENTO: str
    NOMBRE: str
    CORREO: Optional[str] = None
    TELEFONO: Optional[str] = None
    EMPRESA: Optional[str] = None
    TIPO_PLAN: Optional[str] = None
    ESTADO: str
    # 'S' = fue una renovacion (ya existia antes); 'N' = alta nueva ese mes.
    RENOVADO: Optional[str] = None
    FECHA_INGRESO: str
    FECHA_FIN: str
    ULTIMO_CONTACTO_FECHA: Optional[str] = None
    ULTIMO_CONTACTO_DESC: Optional[str] = None
    # Color que el equipo le asigna a mano a la fila (ver TitularColor);
    # None = sin colorear.
    COLOR: Optional[str] = None


class ResumenRenovacionesMes(BaseModel):
    anio: int
    mes: int
    total: int
    renovados: int
    altas_nuevas: int
    activos: int
    inactivos: int
    vencen: int = 0


class ListadoRenovacionesMes(BaseModel):
    resumen: ResumenRenovacionesMes
    items: list[RenovacionMesItem]
    # Titulares activos cuyo plan vence (ingreso + 12 meses) en ese mes.
    vencen: list[RenovacionMesItem] = []


class TitularColorActualizar(BaseModel):
    """PUT .../titulares-beneficiarios/{id}/color. COLOR=None quita el color
    (la fila vuelve a mostrarse sin colorear)."""

    COLOR: Optional[str] = None

    @field_validator("COLOR")
    @classmethod
    def _validar_color(cls, valor: Optional[str]) -> Optional[str]:
        if valor is not None and not _PATRON_COLOR_HEX.match(valor):
            raise ValueError("COLOR debe ser un hex de 6 digitos, ej. '#FCA5A5'")
        return valor


class BeneficiarioDetalle(BaseModel):
    ID: int
    TIPO_DOCUMENTO: Optional[str] = None
    DOCUMENTO: Optional[str] = None
    NOMBRE1: Optional[str] = None
    NOMBRE2: Optional[str] = None
    APELLIDO1: Optional[str] = None
    APELLIDO2: Optional[str] = None
    FECHA_NACIMIENTO: Optional[str] = None
    SEXO: Optional[str] = None
    DIRECCION: Optional[str] = None
    CIUDAD: Optional[str] = None
    DEPARTAMENTO: Optional[str] = None
    CORREO: Optional[str] = None
    TELEFONO: Optional[str] = None
    FECHA_INGRESO: Optional[str] = None
    EMPRESA: Optional[str] = None
    TIPO_PLAN: Optional[str] = None
    ESTADO: Optional[str] = None


class BeneficiarioCrear(EntradaMayusculas):
    """EMPRESA, TIPO_PLAN y PLAN_NOMBRE no se piden aqui: el beneficiario
    siempre hereda esos datos del titular al que se asocia (ver
    TitularesBeneficiariosService.crear_beneficiario)."""

    TIPO_DOCUMENTO: str
    DOCUMENTO: str
    NOMBRE1: str
    NOMBRE2: Optional[str] = None
    APELLIDO1: str
    APELLIDO2: Optional[str] = None
    FECHA_NACIMIENTO: date
    SEXO: Optional[str] = None
    DIRECCION: Optional[str] = None
    CIUDAD: str
    DEPARTAMENTO: str
    CORREO: Optional[str] = None
    TELEFONO: Optional[str] = None
    EPS: Optional[str] = None
    OTRAEPS: Optional[str] = None
    PLAN_SALUD: Optional[str] = None
    # False solo desde la carga masiva por Excel (ver frontend: cargaMasiva.ts): un alta
    # manual individual si manda el correo de bienvenida, una importacion de muchos no.
    ENVIAR_CORREO_BIENVENIDA: bool = True


class CreacionBeneficiarioResultado(BaseModel):
    beneficiario: BeneficiarioDetalle
    usuario_servinte_creado: bool
    marcado_en_incle: bool


class BeneficiarioActivar(BaseModel):
    FECHA_INGRESO: date


class BeneficiarioActivarOpciones(BaseModel):
    """POST .../{id_titular}/beneficiarios/{id_beneficiario}/activar: a
    diferencia de BeneficiarioActivar (activacion masiva por documento), aqui
    FECHA_INGRESO no se pide -- se sigue resolviendo del titular, como
    siempre. Solo agrega el toggle de correo."""

    ENVIAR_CORREO_BIENVENIDA: bool = True


class ActivacionBeneficiarioResultado(BaseModel):
    beneficiario: BeneficiarioDetalle
    registros_incle_desmarcados: int


class DesactivacionBeneficiarioResultado(BaseModel):
    beneficiario: BeneficiarioDetalle
    registros_incle_marcados: int


class BeneficiarioUpdate(EntradaMayusculas):
    TIPO_DOCUMENTO: Optional[str] = None
    DOCUMENTO: Optional[str] = None
    NOMBRE1: Optional[str] = None
    NOMBRE2: Optional[str] = None
    APELLIDO1: Optional[str] = None
    APELLIDO2: Optional[str] = None
    FECHA_NACIMIENTO: Optional[date] = None
    SEXO: Optional[str] = None
    DIRECCION: Optional[str] = None
    CIUDAD: Optional[str] = None
    DEPARTAMENTO: Optional[str] = None
    CORREO: Optional[str] = None
    TELEFONO: Optional[str] = None
    EMPRESA: Optional[str] = None
    ESTADO: Optional[str] = None


class CambioTitularBeneficiario(EntradaMayusculas):
    """Documento (cedula) del titular al que se va a mover el beneficiario."""

    DOCUMENTO_TITULAR_NUEVO: str


class ReemplazoBeneficiarioResultado(BaseModel):
    beneficiario_anterior_id: int
    beneficiario_nuevo: BeneficiarioDetalle
    usuario_servinte_creado: bool
    marcado_en_incle: bool
    registros_incle_marcados_anterior: int