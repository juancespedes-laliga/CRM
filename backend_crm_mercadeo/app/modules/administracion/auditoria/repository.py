from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import and_, case, func, or_, select, text
from sqlalchemy.orm import Session, aliased

from app.models import Auditoria, PlanLiga, Usuario

# Tope de filas por pagina (la exportacion a Excel pide todo de una vez).
LIMITE_CAMBIOS = 20000

MODULOS_PLAN_LIGA = ("titulares", "beneficiarios")
ORIGENES_MASIVOS = ("excel", "grupo")

# Titular del grupo (nombre y documento del titular en beneficiarios).
_Titular = aliased(PlanLiga)


@dataclass
class FiltrosCambios:
    modulos: list[str] | None = None
    desde: datetime | None = None
    hasta: datetime | None = None
    buscar: str | None = None
    accion: str | None = None
    origen: str | None = None
    # 0 = proceso automatico (sin usuario).
    usuario: int | None = None
    # Valor tal como se guarda en la tabla (A / I / ...).
    estado: str | None = None
    renovado: bool | None = None


class AuditoriaRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def _con_joins(stmt):
        return stmt.outerjoin(Usuario, Usuario.id == Auditoria.id_usuario).outerjoin(
            _Titular, _Titular.id == Auditoria.id_titular
        )

    def _consulta_cambios(self):
        # id del registro afectado segun el modulo (compatibilidad con el front).
        registro_id = case(
            (Auditoria.modulo == "beneficiarios", Auditoria.id_beneficiario),
            else_=Auditoria.id_titular,
        ).label("registro_id")
        return self._con_joins(
            select(
                Auditoria,
                registro_id,
                Usuario.usuario.label("login"),
                Usuario.nombres.label("nombres"),
                _Titular.nombre1.label("t_nombre1"),
                _Titular.nombre2.label("t_nombre2"),
                _Titular.apellido1.label("t_apellido1"),
                _Titular.apellido2.label("t_apellido2"),
                _Titular.documento.label("t_documento"),
            )
        )

    @staticmethod
    def _condiciones_base(f: FiltrosCambios) -> list:
        """Modulo y rango de fechas: definen el universo de la vista."""
        c = []
        if f.modulos:
            c.append(Auditoria.modulo.in_(f.modulos))
        if f.desde:
            c.append(Auditoria.fecha_actualizacion >= f.desde)
        if f.hasta:
            c.append(Auditoria.fecha_actualizacion < f.hasta)
        return c

    def _condiciones(self, f: FiltrosCambios) -> list:
        c = self._condiciones_base(f)
        if f.accion:
            c.append(Auditoria.accion == f.accion)
        if f.origen:
            c.append(Auditoria.origen == f.origen)
        if f.usuario is not None:
            c.append(
                Auditoria.id_usuario.is_(None) if f.usuario == 0 else Auditoria.id_usuario == f.usuario
            )
        if f.estado:
            c.append(Auditoria.estado_despues == f.estado)
        if f.renovado is not None:
            c.append(Auditoria.modulo.in_(MODULOS_PLAN_LIGA))
            c.append(Auditoria.renovado == "S" if f.renovado else Auditoria.renovado != "S")
        q = (f.buscar or "").strip()
        if q:
            texto = q.upper()
            # En Oracle NULL || 'x' = 'x', asi que los nombres vacios no anulan el texto.
            nombre_titular = (
                _Titular.nombre1 + " " + _Titular.nombre2 + " " + _Titular.apellido1 + " " + _Titular.apellido2
            )
            opciones = [
                func.upper(col).contains(texto, autoescape=True)
                for col in (
                    Auditoria.documento,
                    Auditoria.registro_nombre,
                    Usuario.usuario,
                    Usuario.nombres,
                    _Titular.documento,
                    nombre_titular,
                )
            ]
            if q.isdigit():
                n = int(q)
                opciones += [Auditoria.id_titular == n, Auditoria.id_beneficiario == n, Auditoria.id == n]
            c.append(or_(*opciones))
        return c

    def resumen_por_modulo(
        self, desde: datetime | None, hasta: datetime | None
    ) -> list[tuple[str, int, datetime | None]]:
        stmt = select(
            Auditoria.modulo, func.count(), func.max(Auditoria.fecha_actualizacion)
        ).group_by(Auditoria.modulo)
        if desde:
            stmt = stmt.where(Auditoria.fecha_actualizacion >= desde)
        if hasta:
            stmt = stmt.where(Auditoria.fecha_actualizacion < hasta)
        return [tuple(f) for f in self.db.execute(stmt).all()]

    def listar_cambios(self, f: FiltrosCambios, pagina: int, por_pagina: int) -> list:
        stmt = (
            self._consulta_cambios()
            .where(*self._condiciones(f))
            .order_by(Auditoria.fecha_actualizacion.desc(), Auditoria.id.desc())
            .offset((pagina - 1) * por_pagina)
            .limit(por_pagina)
        )
        return list(self.db.execute(stmt).all())

    def resumen_cambios(self, f: FiltrosCambios) -> dict[str, int]:
        """Totales de las tarjetas sobre todo lo que cumple los filtros (no solo la pagina)."""

        def contar(cond):
            return func.coalesce(func.sum(case((cond, 1), else_=0)), 0)

        stmt = self._con_joins(
            select(
                func.count(),
                func.count(func.distinct(func.coalesce(Auditoria.id_usuario, 0))),
                contar(
                    and_(
                        Auditoria.estado_antes.is_not(None),
                        or_(
                            Auditoria.estado_despues.is_(None),
                            Auditoria.estado_antes != Auditoria.estado_despues,
                        ),
                    )
                ),
                contar(Auditoria.accion == "renovacion"),
                contar(Auditoria.origen.in_(ORIGENES_MASIVOS)),
            ).select_from(Auditoria)
        ).where(*self._condiciones(f))
        total, usuarios, estado, renov, masivos = self.db.execute(stmt).one()
        return {
            "total": int(total or 0),
            "usuarios": int(usuarios or 0),
            "cambios_estado": int(estado or 0),
            "renovaciones": int(renov or 0),
            "masivos": int(masivos or 0),
        }

    def usuarios_cambios(self, f: FiltrosCambios) -> list[tuple[int | None, str | None, str | None]]:
        """Usuarios que aparecen en la vista (para el filtro Usuario)."""
        stmt = (
            select(Auditoria.id_usuario, Usuario.usuario, Usuario.nombres)
            .outerjoin(Usuario, Usuario.id == Auditoria.id_usuario)
            .where(*self._condiciones_base(f))
            .distinct()
        )
        return [tuple(r) for r in self.db.execute(stmt).all()]

    def estados_cambios(self, f: FiltrosCambios) -> list[str]:
        """Estados resultantes que aparecen en la vista (para el filtro Estado)."""
        stmt = (
            select(Auditoria.estado_despues)
            .where(*self._condiciones_base(f), Auditoria.estado_despues.is_not(None))
            .distinct()
        )
        return [r[0] for r in self.db.execute(stmt).all()]

    def obtener_cambio(self, id_cambio: int):
        stmt = self._consulta_cambios().where(Auditoria.id == id_cambio)
        return self.db.execute(stmt).first()

    def historial(self, modulo: str, registro_id: int) -> list:
        if modulo == "beneficiarios":
            condicion = Auditoria.id_beneficiario == registro_id
        else:
            condicion = Auditoria.id_titular == registro_id
        stmt = (
            self._consulta_cambios()
            .where(Auditoria.modulo == modulo, condicion)
            .order_by(Auditoria.fecha_actualizacion.desc(), Auditoria.id.desc())
        )
        return list(self.db.execute(stmt).all())

    def ultimas_renovaciones(self) -> dict[tuple[str, int], tuple[str | None, str | None]]:
        """(modulo, registro_id) -> (nombre, login) de quien hizo la ultima renovacion."""
        registro_id = case(
            (Auditoria.modulo == "beneficiarios", Auditoria.id_beneficiario),
            else_=Auditoria.id_titular,
        )
        stmt = (
            select(Auditoria.modulo, registro_id, Usuario.nombres, Usuario.usuario)
            .outerjoin(Usuario, Usuario.id == Auditoria.id_usuario)
            .where(
                Auditoria.modulo.in_(["titulares", "beneficiarios"]),
                Auditoria.accion.in_(["renovacion", "activacion"]),
                Auditoria.renovado == "S",
            )
            .order_by(Auditoria.fecha_actualizacion.desc(), Auditoria.id.desc())
        )
        resultado: dict[tuple[str, int], tuple[str | None, str | None]] = {}
        for modulo, reg_id, nombres, login in self.db.execute(stmt).all():
            if reg_id is None:
                continue
            resultado.setdefault((modulo, int(reg_id)), (nombres, login))
        return resultado

    # Titulares y beneficiarios con fecha de ingreso. Vencimiento = un anio
    # despues de FECHA_INGRESO: misma regla que Renovaciones por mes (ver titulares_beneficiarios/repository.py).
    _SQL_RENOVACIONES = """
        SELECT 'titular' AS TIPO, p.ID, p.NOMBRE1, p.NOMBRE2, p.APELLIDO1, p.APELLIDO2,
               p.DOCUMENTO, p.EMPRESA,
               NVL(tp.NOMBRE || CASE WHEN tp.CATEGORIA IS NOT NULL THEN ' - ' || tp.CATEGORIA END, p.TIPO_PLAN) AS PLAN,
               p.ESTADO, TRUNC(p.FECHA_INGRESO) AS FECHA_INGRESO, p.RENOVADO,
               NULL AS FECHA_RENOVADO,
               TRUNC(ADD_MONTHS(p.FECHA_INGRESO, 12)) AS VENCIMIENTO,
               NULL AS TITULAR_ID, NULL AS T_NOMBRE1, NULL AS T_NOMBRE2, NULL AS T_APELLIDO1, NULL AS T_APELLIDO2,
               p.TIPO_PLAN AS TIPO_PLAN
        FROM INTRANET_PLANLIGA p
        LEFT JOIN INTRANET_PLANLIGA_TIPO_PLAN tp ON tp.ID = p.TIPO_PLAN_ID
        WHERE p.FECHA_INGRESO IS NOT NULL {filtro_t}
        UNION ALL
        SELECT 'beneficiario', b.ID, b.NOMBRE1, b.NOMBRE2, b.APELLIDO1, b.APELLIDO2,
               b.DOCUMENTO, NVL(b.EMPRESA, p.EMPRESA),
               NVL(tp.NOMBRE || CASE WHEN tp.CATEGORIA IS NOT NULL THEN ' - ' || tp.CATEGORIA END,
                   NVL(TRIM(b.TIPO_PLAN), p.TIPO_PLAN)),
               b.ESTADO, TRUNC(b.FECHA_INGRESO), b.RENOVADO, NULL,
               TRUNC(ADD_MONTHS(b.FECHA_INGRESO, 12)),
               p.ID, p.NOMBRE1, p.NOMBRE2, p.APELLIDO1, p.APELLIDO2,
               NVL(TRIM(b.TIPO_PLAN), p.TIPO_PLAN)
        FROM INTRANET_PLANLIGA_BENEFICIARIO b
        LEFT JOIN INTRANET_PLANLIGA p ON p.ID = b.PLANLIGA_ID
        LEFT JOIN INTRANET_PLANLIGA_TIPO_PLAN tp ON tp.ID = p.TIPO_PLAN_ID
        WHERE b.FECHA_INGRESO IS NOT NULL {filtro_b}
    """

    def listar_renovaciones(self, tipo: str | None) -> list[dict]:
        sql = self._SQL_RENOVACIONES.format(
            filtro_t="AND 1 = 0" if tipo == "beneficiario" else "",
            filtro_b="AND 1 = 0" if tipo == "titular" else "",
        )
        return [
            {k.lower(): v for k, v in f.items()}
            for f in self.db.execute(text(sql)).mappings().all()
        ]
