from datetime import date, datetime
from typing import Iterator

from sqlalchemy import (
    ColumnElement,
    String,
    case,
    cast,
    func,
    literal_column,
    or_,
    select,
    text,
    update,
)
from sqlalchemy.orm import Session

from app.models import PlanLiga, PlanLigaBeneficiario, PlanLigaTipoPlan, TitularColor, Usuario

ESTADO_ACTIVO = "A"
ESTADO_INACTIVO = "I"
ESTADOS_FILTRO = {"activo": ESTADO_ACTIVO, "inactivo": ESTADO_INACTIVO}

# El Plan Estandar (base implicita, sin fila propia en el catalogo) es de 4
# beneficiarios + 1 titular. Cuando un tipo_plan tiene beneficiarios_adicionales
# (> 0), esos adicionales se suman sobre esa base fija, no sobre la columna
# BENEFICIARIOS de esa fila (que en los planes "X Adicional" no representa el
# cupo total, sino solo el incremento). Si no tiene adicionales, el cupo es
# directamente el valor de BENEFICIARIOS de ese tipo_plan.
BENEFICIARIOS_PLAN_ESTANDAR = 4

RANGOS_EDAD: dict[str, tuple[int, int | None]] = {
    "0-17": (0, 17),
    "18-35": (18, 35),
    "36-50": (36, 50),
    "51+": (51, None),
}

# Solo los campos de interes para Mercadeo son editables por API; los legacy
# de plan (tipo_plan, eps, plan_nombre, etc.) y los de sistema/auditoria
# quedan afuera a proposito (ver conversacion sobre columnas expuestas).
CAMPOS_TITULAR_EDITABLES = {
    "DOCUMENTO": "documento",
    "TIPO_DOCUMENTO": "tipo",
    "NOMBRE1": "nombre1",
    "NOMBRE2": "nombre2",
    "APELLIDO1": "apellido1",
    "APELLIDO2": "apellido2",
    "FECHA_NACIMIENTO": "fecha_nacimiento",
    "SEXO": "sexo",
    "CORREO": "correo",
    "TELEFONO": "telefono",
    "DIRECCION": "direccion",
    "CIUDAD": "ciudad",
    "DEPARTAMENTO": "departamento",
    "EMPRESA": "empresa",
    "ESTADO": "estado",
}

CAMPOS_TITULAR_CREACION = {
    "TIPO_PLAN": "tipo_plan",
    "TIPO_PLAN_ID": "tipo_plan_id",
    "TIPO_DOCUMENTO": "tipo",
    "DOCUMENTO": "documento",
    "NOMBRE1": "nombre1",
    "NOMBRE2": "nombre2",
    "APELLIDO1": "apellido1",
    "APELLIDO2": "apellido2",
    "FECHA_NACIMIENTO": "fecha_nacimiento",
    "SEXO": "sexo",
    "DIRECCION": "direccion",
    "CIUDAD": "ciudad",
    "DEPARTAMENTO": "departamento",
    "CORREO": "correo",
    "TELEFONO": "telefono",
    "TIPO_AFILIADO": "tipo_afiliado",
    "EMPRESA": "empresa",
    "EPS": "eps",
    "OTRAEPS": "otraeps",
    "PLAN_SALUD": "plan_salud",
    "PLAN_NOMBRE": "plan_nombre",
}

CAMPOS_BENEFICIARIO_CREACION = {
    "TIPO_DOCUMENTO": "tipo",
    "DOCUMENTO": "documento",
    "NOMBRE1": "nombre1",
    "NOMBRE2": "nombre2",
    "APELLIDO1": "apellido1",
    "APELLIDO2": "apellido2",
    "FECHA_NACIMIENTO": "fecha_nacimiento",
    "SEXO": "sexo",
    "DIRECCION": "direccion",
    "CIUDAD": "ciudad",
    "DEPARTAMENTO": "departamento",
    "CORREO": "correo",
    "TELEFONO": "telefono",
    "EPS": "eps",
    "OTRAEPS": "otraeps",
    "PLAN_SALUD": "plan_salud",
}

CAMPOS_BENEFICIARIO_EDITABLES = {
    "TIPO_DOCUMENTO": "tipo",
    "DOCUMENTO": "documento",
    "NOMBRE1": "nombre1",
    "NOMBRE2": "nombre2",
    "APELLIDO1": "apellido1",
    "APELLIDO2": "apellido2",
    "FECHA_NACIMIENTO": "fecha_nacimiento",
    "SEXO": "sexo",
    "DIRECCION": "direccion",
    "CIUDAD": "ciudad",
    "DEPARTAMENTO": "departamento",
    "CORREO": "correo",
    "TELEFONO": "telefono",
    "EMPRESA": "empresa",
    "ESTADO": "estado",
}


def _fecha_iso(valor) -> str | None:
    """Normaliza date/datetime (lo que trae oracledb para columnas DATE) a
    'YYYY-MM-DD'; usado solo por las consultas con SQL crudo (text()) de esta
    clase, ya que las armadas con select()/func.to_char() no lo necesitan."""
    if valor is None:
        return None
    if isinstance(valor, datetime):
        return valor.date().isoformat()
    if isinstance(valor, date):
        return valor.isoformat()
    return str(valor)


def _rango_fecha_nacimiento(edad: str, hoy: date) -> tuple[date | None, date | None]:
    edad_min, edad_max = RANGOS_EDAD[edad]
    fecha_nacimiento_max = hoy.replace(year=hoy.year - edad_min)
    fecha_nacimiento_min = (
        hoy.replace(year=hoy.year - edad_max - 1) if edad_max is not None else None
    )
    return fecha_nacimiento_min, fecha_nacimiento_max


def _nombre_plan() -> ColumnElement:
    """Nombre del tipo de plan + su categoria (ej. 'Plan Liga - 6 Beneficiarios')."""
    return PlanLigaTipoPlan.nombre + case(
        (
            PlanLigaTipoPlan.categoria.isnot(None),
            literal_column("' - '") + PlanLigaTipoPlan.categoria,
        ),
        else_=literal_column("''"),
    )


def _cupo_plan() -> ColumnElement:
    """Cupo total de beneficiarios del tipo_plan (ver BENEFICIARIOS_PLAN_ESTANDAR).

    Requiere que PlanLiga este outer-joineado con PlanLigaTipoPlan: si el
    titular no tiene tipo_plan_id (Plan Estandar implicito, sin fila propia
    en el catalogo), el cupo es la base fija.

    Si el tipo_plan tiene BENEFICIARIOS = 0 y sin adicionales (ej. "Empresarial
    Individual"), el cupo de beneficiarios queda en 0: el plan es "1 de 1"
    (solo el titular, sin espacio para beneficiarios).
    """
    return case(
        (PlanLiga.tipo_plan_id.is_(None), BENEFICIARIOS_PLAN_ESTANDAR),
        (
            PlanLigaTipoPlan.beneficiarios_adicionales > 0,
            BENEFICIARIOS_PLAN_ESTANDAR + PlanLigaTipoPlan.beneficiarios_adicionales,
        ),
        else_=func.coalesce(PlanLigaTipoPlan.beneficiarios, 0),
    )


def _columnas_beneficiario() -> list[ColumnElement]:
    return [
        PlanLigaBeneficiario.id.label("ID"),
        PlanLigaBeneficiario.tipo.label("TIPO_DOCUMENTO"),
        PlanLigaBeneficiario.documento.label("DOCUMENTO"),
        PlanLigaBeneficiario.nombre1.label("NOMBRE1"),
        PlanLigaBeneficiario.nombre2.label("NOMBRE2"),
        PlanLigaBeneficiario.apellido1.label("APELLIDO1"),
        PlanLigaBeneficiario.apellido2.label("APELLIDO2"),
        func.to_char(PlanLigaBeneficiario.fecha_nacimiento, "YYYY-MM-DD").label(
            "FECHA_NACIMIENTO"
        ),
        PlanLigaBeneficiario.sexo.label("SEXO"),
        PlanLigaBeneficiario.direccion.label("DIRECCION"),
        PlanLigaBeneficiario.ciudad.label("CIUDAD"),
        PlanLigaBeneficiario.departamento.label("DEPARTAMENTO"),
        PlanLigaBeneficiario.correo.label("CORREO"),
        PlanLigaBeneficiario.telefono.label("TELEFONO"),
        func.to_char(PlanLigaBeneficiario.fecha_ingreso, "DD/MM/YYYY").label(
            "FECHA_INGRESO"
        ),
        PlanLigaBeneficiario.empresa.label("EMPRESA"),
        # Si el beneficiario no tiene tipo_plan propio, se muestra el del titular.
        func.coalesce(
            func.nullif(func.trim(PlanLigaBeneficiario.tipo_plan), ""),
            PlanLiga.tipo_plan,
        ).label("TIPO_PLAN"),
        PlanLigaBeneficiario.estado.label("ESTADO"),
    ]


class TitularesBeneficiariosRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def obtener_titular(self, id_titular: int) -> dict | None:
        stmt = select(
            PlanLiga.id.label("ID_TITULAR"),
            PlanLiga.documento.label("DOCUMENTO"),
            PlanLiga.tipo.label("TIPO_DOCUMENTO"),
            PlanLiga.nombre1.label("NOMBRE1"),
            PlanLiga.nombre2.label("NOMBRE2"),
            PlanLiga.apellido1.label("APELLIDO1"),
            PlanLiga.apellido2.label("APELLIDO2"),
            func.to_char(PlanLiga.fecha_nacimiento, "DD/MM/YYYY").label(
                "FECHA_NACIMIENTO"
            ),
            PlanLiga.sexo.label("SEXO"),
            PlanLiga.correo.label("CORREO"),
            PlanLiga.telefono.label("TELEFONO"),
            PlanLiga.direccion.label("DIRECCION"),
            PlanLiga.ciudad.label("CIUDAD"),
            PlanLiga.departamento.label("DEPARTAMENTO"),
            PlanLiga.tipo_plan.label("TIPO_PLAN"),
            PlanLiga.tipo_plan_id.label("TIPO_PLAN_ID"),
            PlanLiga.tipo_afiliado.label("TIPO_AFILIADO"),
            PlanLiga.empresa.label("EMPRESA"),
            PlanLiga.eps.label("EPS"),
            PlanLiga.otraeps.label("OTRAEPS"),
            PlanLiga.plan_salud.label("PLAN_SALUD"),
            PlanLiga.plan_nombre.label("PLAN_NOMBRE"),
            PlanLiga.estado.label("ESTADO"),
            func.to_char(PlanLiga.fecha_ingreso, "DD/MM/YYYY").label("FECHA_INGRESO"),
        ).where(PlanLiga.id == id_titular)

        fila = self.db.execute(stmt).mappings().first()
        return dict(fila) if fila is not None else None

    def obtener_fecha_ingreso_titular(self, id_titular: int) -> date | None:
        titular = self.db.get(PlanLiga, id_titular)
        return titular.fecha_ingreso if titular else None

    def listar_beneficiarios(self, id_titular: int, estado: str | None = None) -> list[dict]:
        condiciones = [PlanLigaBeneficiario.planliga_id == id_titular]

        if estado:
            codigo = estado.strip().upper()
            if codigo in (ESTADO_ACTIVO, ESTADO_INACTIVO):
                condiciones.append(PlanLigaBeneficiario.estado == codigo)
            else:
                # Compat: "activo" / "inactivo"
                mapeado = ESTADOS_FILTRO.get(estado.strip().lower())
                if mapeado:
                    condiciones.append(PlanLigaBeneficiario.estado == mapeado)

        stmt = (
            select(*_columnas_beneficiario())
            .outerjoin(PlanLiga, PlanLiga.id == PlanLigaBeneficiario.planliga_id)
            .where(*condiciones)
            .order_by(PlanLigaBeneficiario.orden, PlanLigaBeneficiario.id)
        )
        return [dict(row) for row in self.db.execute(stmt).mappings().all()]


    def obtener_beneficiario(self, id_titular: int, id_beneficiario: int) -> dict | None:
        stmt = (
            select(*_columnas_beneficiario())
            .outerjoin(PlanLiga, PlanLiga.id == PlanLigaBeneficiario.planliga_id)
            .where(
                PlanLigaBeneficiario.id == id_beneficiario,
                PlanLigaBeneficiario.planliga_id == id_titular,
            )
        )

        fila = self.db.execute(stmt).mappings().first()
        return dict(fila) if fila is not None else None

    def obtener_beneficiario_por_id(self, id_beneficiario: int) -> dict | None:
        stmt = (
            select(
                *_columnas_beneficiario(),
                PlanLigaBeneficiario.planliga_id.label("PLANLIGA_ID"),
            )
            .outerjoin(PlanLiga, PlanLiga.id == PlanLigaBeneficiario.planliga_id)
            .where(PlanLigaBeneficiario.id == id_beneficiario)
        )
        fila = self.db.execute(stmt).mappings().first()
        return dict(fila) if fila is not None else None

    def buscar_beneficiario_por_documento(self, documento: str) -> dict | None:
        stmt = select(
            PlanLigaBeneficiario.id.label("ID"),
            PlanLigaBeneficiario.planliga_id.label("PLANLIGA_ID"),
        ).where(PlanLigaBeneficiario.documento == documento)
        fila = self.db.execute(stmt).mappings().first()
        return dict(fila) if fila is not None else None

    def buscar_titulares_por_documento(self, documento: str) -> list[dict]:
        stmt = select(
            PlanLiga.id.label("ID_TITULAR"),
            PlanLiga.estado.label("ESTADO"),
        ).where(PlanLiga.documento == documento)
        return [dict(row) for row in self.db.execute(stmt).mappings().all()]

    def listar_planes(self) -> list[PlanLigaTipoPlan]:
        stmt = (
            select(PlanLigaTipoPlan)
            .where(PlanLigaTipoPlan.estado == ESTADO_ACTIVO)
            .order_by(PlanLigaTipoPlan.nombre)
        )
        return list(self.db.scalars(stmt))

    def listar_nombres_planes(self) -> list[dict]:
        stmt = (
            select(PlanLigaTipoPlan.id.label("ID"), _nombre_plan().label("NOMBRE"))
            .where(PlanLigaTipoPlan.estado == ESTADO_ACTIVO)
            .order_by(PlanLigaTipoPlan.nombre, PlanLigaTipoPlan.categoria)
        )
        return [dict(row) for row in self.db.execute(stmt).mappings().all()]

    def contar_titulares_activos(self) -> int:
        stmt = select(func.count()).select_from(PlanLiga).where(
            PlanLiga.estado == ESTADO_ACTIVO
        )
        return self.db.scalar(stmt) or 0

    def contar_beneficiarios_activos(self) -> int:
        stmt = select(func.count()).select_from(PlanLigaBeneficiario).where(
            PlanLigaBeneficiario.estado == ESTADO_ACTIVO
        )
        return self.db.scalar(stmt) or 0

    def _construir_condiciones(
        self,
        estado: str | None = None,
        tipo_plan_id: str | None = None,
        sexo: str | None = None,
        edad: str | None = None,
        busqueda: str | None = None,
    ) -> list[ColumnElement]:
        estado = None if estado and estado.strip().lower() == "todos" else estado
        tipo_plan_id = None if tipo_plan_id and tipo_plan_id.strip().lower() == "todos" else tipo_plan_id
        sexo = None if sexo and sexo.strip().lower() == "todos" else sexo
        edad = None if edad and edad.strip().lower() == "todos" else edad

        condiciones = []

        if estado:
            codigo = ESTADOS_FILTRO.get(estado.lower())
            if codigo:
                condiciones.append(PlanLiga.estado == codigo)

        if tipo_plan_id and tipo_plan_id.strip():
            valor = tipo_plan_id.strip()
            if valor.lower() == "null":
                condiciones.append(PlanLiga.tipo_plan_id.is_(None))
            else:
                condiciones.append(PlanLiga.tipo_plan_id == int(valor))

        if sexo:
            condiciones.append(func.upper(PlanLiga.sexo) == sexo.upper())

        if edad:
            fecha_min, fecha_max = _rango_fecha_nacimiento(edad, date.today())
            condiciones.append(PlanLiga.fecha_nacimiento <= fecha_max)
            if fecha_min is not None:
                condiciones.append(PlanLiga.fecha_nacimiento > fecha_min)

        if busqueda and busqueda.strip():
            # Se colapsan espacios repetidos (' +' -> ' ') porque nombre2/apellido2
            # suelen venir NULL: el coalesce a "" deja un espacio "vacio" entre
            # partes (ej. "ARGENIS" + " " + "" + " " + "GALINDEZ" = doble espacio),
            # y sin normalizar eso, buscar el nombre completo con espacios simples
            # no hacia match aunque buscar una sola palabra si funcionara.
            termino = f"%{' '.join(busqueda.split()).upper()}%"
            nombre_completo = func.regexp_replace(
                func.coalesce(PlanLiga.nombre1, "")
                + literal_column("' '")
                + func.coalesce(PlanLiga.nombre2, "")
                + literal_column("' '")
                + func.coalesce(PlanLiga.apellido1, "")
                + literal_column("' '")
                + func.coalesce(PlanLiga.apellido2, ""),
                literal_column("' +'"),
                literal_column("' '"),
            )
            nombre_completo_beneficiario = func.regexp_replace(
                func.coalesce(PlanLigaBeneficiario.nombre1, "")
                + literal_column("' '")
                + func.coalesce(PlanLigaBeneficiario.nombre2, "")
                + literal_column("' '")
                + func.coalesce(PlanLigaBeneficiario.apellido1, "")
                + literal_column("' '")
                + func.coalesce(PlanLigaBeneficiario.apellido2, ""),
                literal_column("' +'"),
                literal_column("' '"),
            )
            condiciones.append(
                or_(
                    func.upper(nombre_completo).like(termino),
                    func.upper(func.coalesce(PlanLiga.documento, "")).like(termino),
                    func.upper(func.coalesce(PlanLiga.empresa, "")).like(termino),
                    func.upper(func.coalesce(PlanLiga.correo, "")).like(termino),
                    func.upper(func.coalesce(PlanLiga.tipo_plan, "")).like(termino),
                    select(PlanLigaBeneficiario.id)
                    .where(
                        PlanLigaBeneficiario.planliga_id == PlanLiga.id,
                        or_(
                            func.upper(nombre_completo_beneficiario).like(termino),
                            func.upper(func.coalesce(PlanLigaBeneficiario.documento, "")).like(
                                termino
                            ),
                            func.upper(func.coalesce(PlanLigaBeneficiario.correo, "")).like(
                                termino
                            ),
                            func.upper(func.coalesce(PlanLigaBeneficiario.tipo_plan, "")).like(
                                termino
                            ),
                        ),
                    )
                    .exists(),
                )
            )

        return condiciones

    def exportar_titulares_beneficiarios(
        self,
        estado: str | None = None,
        tipo_plan_id: str | None = None,
        sexo: str | None = None,
        edad: str | None = None,
        busqueda: str | None = None,
    ) -> Iterator[dict]:
        """Titulares que cumplen los filtros, cada uno seguido de sus
        beneficiarios. Sin paginar: trae todo lo que matchee los filtros."""
        condiciones = self._construir_condiciones(estado, tipo_plan_id, sexo, edad, busqueda)

        stmt_titulares = (
            select(
                PlanLiga.id.label("ID_TITULAR"),
                literal_column("'TITULAR'").label("TIPO_REGISTRO"),
                PlanLiga.tipo.label("TIPO_DOCUMENTO"),
                PlanLiga.documento.label("DOCUMENTO"),
                PlanLiga.nombre1.label("NOMBRE1"),
                PlanLiga.nombre2.label("NOMBRE2"),
                PlanLiga.apellido1.label("APELLIDO1"),
                PlanLiga.apellido2.label("APELLIDO2"),
                PlanLiga.empresa.label("EMPRESA"),
                _nombre_plan().label("PLAN"),
                PlanLiga.telefono.label("TELEFONO"),
                PlanLiga.correo.label("CORREO"),
                func.to_char(PlanLiga.fecha_ingreso, "DD/MM/YYYY").label("FECHA_INGRESO"),
                PlanLiga.estado.label("ESTADO"),
            )
            .select_from(PlanLiga)
            .outerjoin(PlanLigaTipoPlan, PlanLigaTipoPlan.id == PlanLiga.tipo_plan_id)
            .where(*condiciones)
            .order_by(PlanLiga.id)
        )

        stmt_beneficiarios = (
            select(
                PlanLigaBeneficiario.planliga_id.label("ID_TITULAR"),
                literal_column("'BENEFICIARIO'").label("TIPO_REGISTRO"),
                PlanLigaBeneficiario.tipo.label("TIPO_DOCUMENTO"),
                PlanLigaBeneficiario.documento.label("DOCUMENTO"),
                PlanLigaBeneficiario.nombre1.label("NOMBRE1"),
                PlanLigaBeneficiario.nombre2.label("NOMBRE2"),
                PlanLigaBeneficiario.apellido1.label("APELLIDO1"),
                PlanLigaBeneficiario.apellido2.label("APELLIDO2"),
                PlanLigaBeneficiario.empresa.label("EMPRESA"),
                PlanLigaBeneficiario.tipo_plan.label("PLAN"),
                PlanLigaBeneficiario.telefono.label("TELEFONO"),
                PlanLigaBeneficiario.correo.label("CORREO"),
                func.to_char(PlanLigaBeneficiario.fecha_ingreso, "DD/MM/YYYY").label(
                    "FECHA_INGRESO"
                ),
                PlanLigaBeneficiario.estado.label("ESTADO"),
            )
            .select_from(PlanLigaBeneficiario)
            .join(PlanLiga, PlanLiga.id == PlanLigaBeneficiario.planliga_id)
            .outerjoin(PlanLigaTipoPlan, PlanLigaTipoPlan.id == PlanLiga.tipo_plan_id)
            .where(*condiciones)
            .order_by(PlanLigaBeneficiario.planliga_id, PlanLigaBeneficiario.orden)
        )

        # Los beneficiarios son pocos frente a los titulares (miles, no
        # millones, en este dominio): se agrupan en memoria por titular para
        # poder intercalarlos sin repetir la consulta de titulares por cada
        # uno (evita el N+1).
        beneficiarios_por_titular: dict[int, list[dict]] = {}
        for fila in self.db.execute(stmt_beneficiarios).mappings():
            beneficiarios_por_titular.setdefault(fila["ID_TITULAR"], []).append(dict(fila))

        for fila_titular in self.db.execute(stmt_titulares).mappings():
            yield dict(fila_titular)
            yield from beneficiarios_por_titular.get(fila_titular["ID_TITULAR"], [])

    def contar_titulares(
        self,
        estado: str | None = None,
        tipo_plan_id: str | None = None,
        sexo: str | None = None,
        edad: str | None = None,
        busqueda: str | None = None,
    ) -> int:
        condiciones = self._construir_condiciones(estado, tipo_plan_id, sexo, edad, busqueda)

        stmt = select(func.count()).select_from(PlanLiga).where(*condiciones)
        return self.db.scalar(stmt) or 0

    def listar_titulares(
        self,
        limit: int = 6,
        offset: int = 0,
        estado: str | None = None,
        tipo_plan_id: str | None = None,
        sexo: str | None = None,
        edad: str | None = None,
        busqueda: str | None = None,
    ) -> list[dict]:
        condiciones = self._construir_condiciones(estado, tipo_plan_id, sexo, edad, busqueda)

        conteo_beneficiarios = func.coalesce(
            select(func.count())
            .select_from(PlanLigaBeneficiario)
            .where(PlanLigaBeneficiario.planliga_id == PlanLiga.id)
            .scalar_subquery(),
            0,
        )
        cupo_plan = _cupo_plan()

        stmt = (
            select(
                PlanLiga.id.label("ID_TITULAR"),
                func.trim(
                    PlanLiga.nombre1
                    + literal_column("' '")
                    + func.coalesce(PlanLiga.nombre2, "")
                    + literal_column("' '")
                    + func.coalesce(PlanLiga.apellido1, "")
                    + literal_column("' '")
                    + func.coalesce(PlanLiga.apellido2, "")
                ).label("TITULAR"),
                PlanLiga.documento.label("DOCUMENTO"),
                PlanLiga.tipo.label("TIPO_DOCUMENTO"),
                PlanLiga.empresa.label("EMPRESA"),
                _nombre_plan().label("PLANES"),
                PlanLiga.tipo_plan.label("TIPO_PLAN"),
                (
                    cast(conteo_beneficiarios, String(50))
                    + literal_column("'/'")
                    + cast(cupo_plan, String(50))
                ).label("BENEFICIARIOS"),
                PlanLiga.correo.label("EMAIL"),
                PlanLiga.telefono.label("TELEFONO"),
                func.to_char(PlanLiga.fecha_ingreso, "DD/MM/YYYY").label("INSCRIPCION"),
                PlanLiga.estado.label("ESTADO"),
            )
            .select_from(PlanLiga)
            .outerjoin(PlanLigaTipoPlan, PlanLigaTipoPlan.id == PlanLiga.tipo_plan_id)
            .where(*condiciones)
            .order_by(PlanLiga.fecha_ingreso.desc())
            .offset(offset)
            .limit(limit)
        )

        return [dict(row) for row in self.db.execute(stmt).mappings().all()]

    def actualizar_titular(self, id_titular: int, datos: dict) -> bool:
        titular = self.db.get(PlanLiga, id_titular)
        if titular is None:
            return False
        for campo, valor in datos.items():
            atributo = CAMPOS_TITULAR_EDITABLES.get(campo)
            if atributo:
                setattr(titular, atributo, valor)
        self.db.commit()
        return True

    def actualizar_beneficiario(
        self, id_titular: int, id_beneficiario: int, datos: dict
    ) -> bool:
        beneficiario = self.db.get(PlanLigaBeneficiario, id_beneficiario)
        if beneficiario is None or beneficiario.planliga_id != id_titular:
            return False
        for campo, valor in datos.items():
            atributo = CAMPOS_BENEFICIARIO_EDITABLES.get(campo)
            if atributo:
                setattr(beneficiario, atributo, valor)
        self.db.commit()
        return True

    def cambiar_titular_beneficiario(
        self,
        id_titular_actual: int,
        id_beneficiario: int,
        id_titular_nuevo: int,
        orden: int,
        tipo_plan: str | None,
        empresa: str | None,
        plan_nombre: str | None,
    ) -> bool:
        """Mueve el beneficiario al nuevo titular heredando tipo_plan, empresa
        y plan_nombre del nuevo titular. FECHA_INGRESO NO se toca: la
        vigencia propia del beneficiario es independiente del titular al que
        quede asociado administrativamente."""
        beneficiario = self.db.get(PlanLigaBeneficiario, id_beneficiario)
        if beneficiario is None or beneficiario.planliga_id != id_titular_actual:
            return False
        beneficiario.planliga_id = id_titular_nuevo
        beneficiario.orden = orden
        beneficiario.tipo_plan = tipo_plan
        beneficiario.empresa = empresa
        beneficiario.plan_nombre = plan_nombre
        self.db.commit()
        return True

    def reemplazar_titular(
        self, id_titular_anterior: int, datos: dict
    ) -> tuple[int, int] | None:
        """Da de alta un titular nuevo (nueva persona) heredando plan y cupo
        del anterior, reasigna los beneficiarios del anterior al nuevo y
        desactiva el anterior. Retorna (id_nuevo, beneficiarios_reasignados)
        o None si el anterior no existe o ya esta inactivo."""
        anterior = self.db.get(PlanLiga, id_titular_anterior)
        if anterior is None or anterior.estado != ESTADO_ACTIVO:
            return None

        campos_nuevos = {
            atributo: datos.get(campo)
            for campo, atributo in CAMPOS_TITULAR_EDITABLES.items()
            if campo != "ESTADO"
        }
        nuevo = PlanLiga(
            **campos_nuevos,
            tipo_plan=anterior.tipo_plan,
            tipo_plan_id=anterior.tipo_plan_id,
            tipo_afiliado=anterior.tipo_afiliado,
            eps=anterior.eps,
            otraeps=anterior.otraeps,
            plan_salud=anterior.plan_salud,
            plan_nombre=anterior.plan_nombre,
            estado=ESTADO_ACTIVO,
            fecha_ingreso=anterior.fecha_ingreso,
            fecha_registro=datetime.now(),
        )
        self.db.add(nuevo)
        self.db.flush()

        stmt = (
            update(PlanLigaBeneficiario)
            .where(
                PlanLigaBeneficiario.planliga_id == id_titular_anterior,
                PlanLigaBeneficiario.estado == ESTADO_ACTIVO,
            )
            .values(planliga_id=nuevo.id)
        )
        resultado = self.db.execute(stmt)

        anterior.estado = ESTADO_INACTIVO

        self.db.commit()
        self.db.refresh(nuevo)
        return nuevo.id, resultado.rowcount

    def reemplazar_beneficiario(
        self, id_titular: int, id_beneficiario_anterior: int, datos: dict
    ) -> int | None:
        """Da de alta un beneficiario nuevo (nueva persona) en el mismo
        titular y orden, heredando plan del anterior, y desactiva el
        anterior. Retorna el id nuevo o None si el anterior no existe, no
        pertenece a ese titular o ya esta inactivo."""
        anterior = self.db.get(PlanLigaBeneficiario, id_beneficiario_anterior)
        if (
            anterior is None
            or anterior.planliga_id != id_titular
            or anterior.estado != ESTADO_ACTIVO
        ):
            return None

        campos_nuevos = {
            atributo: datos.get(campo)
            for campo, atributo in CAMPOS_BENEFICIARIO_EDITABLES.items()
            if campo != "ESTADO"
        }
        nuevo = PlanLigaBeneficiario(
            **campos_nuevos,
            planliga_id=id_titular,
            tipo_plan=anterior.tipo_plan,
            eps=anterior.eps,
            otraeps=anterior.otraeps,
            plan_salud=anterior.plan_salud,
            plan_nombre=anterior.plan_nombre,
            orden=anterior.orden,
            estado=ESTADO_ACTIVO,
            tipo_afiliado=anterior.tipo_afiliado,
            fecha_ingreso=anterior.fecha_ingreso,
            fecha_registro=datetime.now(),
            renovado="N",  # ver comentario en crear_beneficiario: NOT NULL sin default aplicable si se manda NULL
        )
        self.db.add(nuevo)

        anterior.estado = ESTADO_INACTIVO

        self.db.commit()
        self.db.refresh(nuevo)
        return nuevo.id

    def existe_documento(self, tipo: str, documento: str) -> str | None:
        """Retorna 'TITULAR', 'BENEFICIARIO' o None si el documento no esta registrado."""
        if (
            self.db.scalar(
                select(PlanLiga.id)
                .where(PlanLiga.tipo == tipo, PlanLiga.documento == documento)
                .limit(1)
            )
            is not None
        ):
            return "TITULAR"

        if (
            self.db.scalar(
                select(PlanLigaBeneficiario.id)
                .where(
                    PlanLigaBeneficiario.tipo == tipo,
                    PlanLigaBeneficiario.documento == documento,
                )
                .limit(1)
            )
            is not None
        ):
            return "BENEFICIARIO"

        return None

    def obtener_usuario_id(self, username: str) -> int | None:
        stmt = select(Usuario.id).where(
            func.upper(func.trim(Usuario.usuario)) == username.strip().upper()
        )
        return self.db.scalar(stmt)

    def crear_titular(self, datos: dict, fecha_ingreso: date) -> int:
        campos = {
            atributo: datos.get(campo)
            for campo, atributo in CAMPOS_TITULAR_CREACION.items()
        }
        titular = PlanLiga(
            **campos,
            estado=ESTADO_ACTIVO,
            fecha_ingreso=fecha_ingreso,
            fecha_registro=datetime.now(),
            renovado="N",
        )
        self.db.add(titular)
        self.db.commit()
        self.db.refresh(titular)
        return titular.id

    def contar_beneficiarios(self, id_titular: int) -> int:
        stmt = select(func.count()).select_from(PlanLigaBeneficiario).where(
            PlanLigaBeneficiario.planliga_id == id_titular,
            PlanLigaBeneficiario.estado == ESTADO_ACTIVO,
        )
        return self.db.scalar(stmt) or 0

    def cupo_beneficiarios_titular(self, id_titular: int) -> int:
        stmt = (
            select(_cupo_plan())
            .select_from(PlanLiga)
            .outerjoin(PlanLigaTipoPlan, PlanLigaTipoPlan.id == PlanLiga.tipo_plan_id)
            .where(PlanLiga.id == id_titular)
        )
        return self.db.scalar(stmt) or 0

    def cupo_de_plan(self, tipo_plan_id: int | None) -> int:
        """Cupo de beneficiarios de un plan candidato (ej. el que se elige al
        renovar), sin depender de que ya este asociado a un titular. Misma
        formula que _cupo_plan(), pero evaluada en Python porque aqui no hay
        una fila de PlanLiga contra la cual outer-joinear."""
        if tipo_plan_id is None:
            return BENEFICIARIOS_PLAN_ESTANDAR
        tipo_plan = self.db.get(PlanLigaTipoPlan, tipo_plan_id)
        if tipo_plan is None:
            return BENEFICIARIOS_PLAN_ESTANDAR
        if tipo_plan.beneficiarios_adicionales and tipo_plan.beneficiarios_adicionales > 0:
            return BENEFICIARIOS_PLAN_ESTANDAR + tipo_plan.beneficiarios_adicionales
        return tipo_plan.beneficiarios or 0

    def siguiente_orden_beneficiario(self, id_titular: int) -> int:
        """ORDEN a asignar al proximo beneficiario del titular: reutiliza el
        menor ORDEN de un beneficiario inactivo (ese cupo quedo libre) si
        existe; si no hay huecos, usa el siguiente consecutivo tras el
        maximo ORDEN ya usado (activo o inactivo)."""
        orden_libre = self.db.scalar(
            select(func.min(PlanLigaBeneficiario.orden)).where(
                PlanLigaBeneficiario.planliga_id == id_titular,
                PlanLigaBeneficiario.estado == ESTADO_INACTIVO,
                PlanLigaBeneficiario.orden.isnot(None),
            )
        )
        if orden_libre is not None:
            return orden_libre

        maximo = self.db.scalar(
            select(func.max(PlanLigaBeneficiario.orden)).where(
                PlanLigaBeneficiario.planliga_id == id_titular,
            )
        )
        return (maximo or 0) + 1

    def crear_beneficiario(
        self,
        id_titular: int,
        datos: dict,
        fecha_ingreso: date,
        orden: int,
        tipo_plan: str | None,
        empresa: str | None,
        plan_nombre: str | None,
    ) -> int:
        campos = {
            atributo: datos.get(campo)
            for campo, atributo in CAMPOS_BENEFICIARIO_CREACION.items()
        }
        beneficiario = PlanLigaBeneficiario(
            **campos,
            planliga_id=id_titular,
            tipo_plan=tipo_plan,
            empresa=empresa,
            plan_nombre=plan_nombre,
            orden=orden,
            estado=ESTADO_ACTIVO,
            tipo_afiliado="2",
            fecha_ingreso=fecha_ingreso,
            fecha_registro=datetime.now(),
            # RENOVADO es NOT NULL en Oracle con DEFAULT 'N', pero ese default solo aplica si la
            # columna se omite del INSERT; SQLAlchemy la manda explicita como NULL si no se fija
            # aca, lo que revienta con ORA-01400 (a diferencia de INTRANET_PLANLIGA, que lo tolera).
            renovado="N",
        )
        self.db.add(beneficiario)
        self.db.commit()
        self.db.refresh(beneficiario)
        return beneficiario.id

    def activar_beneficiario(
        self, id_titular: int, id_beneficiario: int, fecha_ingreso: date
    ) -> bool:
        beneficiario = self.db.get(PlanLigaBeneficiario, id_beneficiario)
        if beneficiario is None or beneficiario.planliga_id != id_titular:
            return False
        beneficiario.estado = ESTADO_ACTIVO
        beneficiario.fecha_ingreso = fecha_ingreso
        self.db.commit()
        return True

    def desactivar_beneficiario(self, id_titular: int, id_beneficiario: int) -> bool:
        beneficiario = self.db.get(PlanLigaBeneficiario, id_beneficiario)
        if beneficiario is None or beneficiario.planliga_id != id_titular:
            return False
        beneficiario.estado = ESTADO_INACTIVO
        self.db.commit()
        return True

    def activar_titular(
        self,
        id_titular: int,
        fecha_ingreso: date,
        cambiar_plan: bool = False,
        tipo_plan: str | None = None,
        tipo_plan_id: int | None = None,
    ) -> bool:
        titular = self.db.get(PlanLiga, id_titular)
        if titular is None:
            return False
        titular.estado = ESTADO_ACTIVO
        titular.fecha_ingreso = fecha_ingreso
        titular.renovado = "S"
        if cambiar_plan:
            titular.tipo_plan = tipo_plan
            titular.tipo_plan_id = tipo_plan_id
        self.db.commit()
        return True

    def activar_beneficiarios(self, id_titular: int, fecha_ingreso: date) -> int:
        stmt = (
            update(PlanLigaBeneficiario)
            .where(PlanLigaBeneficiario.planliga_id == id_titular)
            .values(
                fecha_ingreso=fecha_ingreso,
                renovado="S",
            )
        )
        resultado = self.db.execute(stmt)
        self.db.commit()
        return resultado.rowcount

    # Cuenta cuantos titulares/beneficiarios ACTIVOS de esa empresa se verian
    # afectados por cambiar_fecha_ingreso_grupo, sin modificar nada: es el
    # preview que se muestra en el dialogo de confirmacion antes de aplicar.
    def contar_grupo_activo(self, empresa: str) -> tuple[int, int]:
        total_titulares = self.db.scalar(
            select(func.count())
            .select_from(PlanLiga)
            .where(PlanLiga.empresa == empresa, PlanLiga.estado == ESTADO_ACTIVO)
        )
        ids_titulares = select(PlanLiga.id).where(
            PlanLiga.empresa == empresa, PlanLiga.estado == ESTADO_ACTIVO
        )
        total_beneficiarios = self.db.scalar(
            select(func.count())
            .select_from(PlanLigaBeneficiario)
            .where(
                PlanLigaBeneficiario.planliga_id.in_(ids_titulares),
                PlanLigaBeneficiario.estado == ESTADO_ACTIVO,
            )
        )
        return total_titulares or 0, total_beneficiarios or 0

    # Cambia FECHA_INGRESO a todos los titulares ACTIVOS de esa empresa y a
    # los beneficiarios ACTIVOS de esos titulares (coincidencia exacta con
    # EMPRESA, no LIKE: el valor viene del selector de razon_social del
    # catalogo de Empresas, que se importa desde este mismo texto).
    #
    # Cambiar la fecha de ingreso en masa es, en la practica, renovar el grupo
    # completo -> tambien se marca RENOVADO = 'S' en titular y beneficiario
    # (mismo criterio que activar_titular / activar_beneficiarios).
    def cambiar_fecha_ingreso_grupo(self, empresa: str, fecha_ingreso: date) -> tuple[int, int]:
        stmt_titulares = (
            update(PlanLiga)
            .where(PlanLiga.empresa == empresa, PlanLiga.estado == ESTADO_ACTIVO)
            .values(fecha_ingreso=fecha_ingreso, renovado="S")
        )
        resultado_titulares = self.db.execute(stmt_titulares)

        ids_titulares = select(PlanLiga.id).where(
            PlanLiga.empresa == empresa, PlanLiga.estado == ESTADO_ACTIVO
        )
        stmt_beneficiarios = (
            update(PlanLigaBeneficiario)
            .where(
                PlanLigaBeneficiario.planliga_id.in_(ids_titulares),
                PlanLigaBeneficiario.estado == ESTADO_ACTIVO,
            )
            .values(fecha_ingreso=fecha_ingreso, renovado="S")
        )
        resultado_beneficiarios = self.db.execute(stmt_beneficiarios)

        self.db.commit()
        return resultado_titulares.rowcount, resultado_beneficiarios.rowcount

    def desactivar_titular(self, id_titular: int) -> bool:
        titular = self.db.get(PlanLiga, id_titular)
        if titular is None:
            return False
        titular.estado = ESTADO_INACTIVO
        self.db.commit()
        return True

    def desactivar_beneficiarios(self, id_titular: int) -> list[tuple[str, str]]:
        stmt_select = select(
            PlanLigaBeneficiario.tipo, PlanLigaBeneficiario.documento
        ).where(
            PlanLigaBeneficiario.planliga_id == id_titular,
            PlanLigaBeneficiario.estado == ESTADO_ACTIVO,
        )
        beneficiarios = [tuple(fila) for fila in self.db.execute(stmt_select).all()]

        stmt_update = (
            update(PlanLigaBeneficiario)
            .where(
                PlanLigaBeneficiario.planliga_id == id_titular,
                PlanLigaBeneficiario.estado == ESTADO_ACTIVO,
            )
            .values(estado=ESTADO_INACTIVO)
        )
        self.db.execute(stmt_update)
        self.db.commit()
        return beneficiarios

    # ---------------------------------------------------------------------
    # Renovaciones por mes: titulares cuyo FECHA_INGRESO cae en el mes
    # consultado (se activaron o renovaron ese mes). RENOVADO distingue
    # renovacion ('S', ya existian) de alta nueva ('N', primera vez).
    # ---------------------------------------------------------------------
    _SQL_RENOVACIONES_MES = """
    SELECT
        p.ID,
        p.TIPO AS TIPO_DOCUMENTO,
        p.DOCUMENTO,
        REGEXP_REPLACE(
            p.NOMBRE1 || ' ' || NVL(p.NOMBRE2, '') || ' ' || p.APELLIDO1 || ' ' || NVL(p.APELLIDO2, ''),
            ' +', ' '
        ) AS NOMBRE,
        p.CORREO,
        p.TELEFONO,
        p.EMPRESA,
        p.TIPO_PLAN,
        p.ESTADO,
        p.RENOVADO,
        TRUNC(p.FECHA_INGRESO) AS FECHA_INGRESO,
        TRUNC(ADD_MONTHS(p.FECHA_INGRESO, 12)) AS FECHA_FIN,
        (
            SELECT MAX(b.FECHA)
            FROM MERCADEO_CRM_BITACORA b
            WHERE b.TITULAR_ID = p.ID
        ) AS ULTIMO_CONTACTO_FECHA,
        (
            SELECT b2.DESCRIPCION
            FROM MERCADEO_CRM_BITACORA b2
            WHERE b2.TITULAR_ID = p.ID
            ORDER BY b2.FECHA DESC
            FETCH FIRST 1 ROW ONLY
        ) AS ULTIMO_CONTACTO_DESC,
        tc.COLOR
    FROM INTRANET_PLANLIGA p
    LEFT JOIN MERCADEO_CRM_TITULAR_COLOR tc ON tc.TITULAR_ID = p.ID
    WHERE p.FECHA_INGRESO IS NOT NULL
      AND EXTRACT(YEAR FROM p.FECHA_INGRESO) = :anio
      AND EXTRACT(MONTH FROM p.FECHA_INGRESO) = :mes
    ORDER BY p.FECHA_INGRESO DESC, NOMBRE
    """

    def listar_renovaciones_mes(self, anio: int, mes: int) -> list[dict]:
        filas = self.db.execute(
            text(self._SQL_RENOVACIONES_MES), {"anio": anio, "mes": mes}
        ).mappings().all()
        resultado = []
        for fila in filas:
            datos = {clave.upper(): valor for clave, valor in fila.items()}
            datos["FECHA_INGRESO"] = _fecha_iso(datos["FECHA_INGRESO"])
            datos["FECHA_FIN"] = _fecha_iso(datos["FECHA_FIN"])
            datos["ULTIMO_CONTACTO_FECHA"] = _fecha_iso(datos["ULTIMO_CONTACTO_FECHA"])
            resultado.append(datos)
        return resultado

    def establecer_color_titular(
        self, id_titular: int, color: str, usuario_id: int | None
    ) -> bool:
        """Upsert: 1 fila por titular como maximo (unique en titular_id, ver
        modelo TitularColor). Retorna False si el titular no existe."""
        if self.db.get(PlanLiga, id_titular) is None:
            return False
        fila = self.db.scalar(
            select(TitularColor).where(TitularColor.titular_id == id_titular)
        )
        if fila is None:
            fila = TitularColor(titular_id=id_titular, color=color, usuario_id=usuario_id)
            self.db.add(fila)
        else:
            fila.color = color
            fila.usuario_id = usuario_id
        self.db.commit()
        return True

    def quitar_color_titular(self, id_titular: int) -> bool:
        fila = self.db.scalar(
            select(TitularColor).where(TitularColor.titular_id == id_titular)
        )
        if fila is None:
            return False
        self.db.delete(fila)
        self.db.commit()
        return True
