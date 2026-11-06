from datetime import datetime

from sqlalchemy import case, func, select, text
from sqlalchemy.orm import Session, aliased

from app.models import Auditoria, PlanLiga, Usuario

# Tope de filas por consulta del log: el front filtra en memoria lo que llega.
LIMITE_CAMBIOS = 5000


class AuditoriaRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _consulta_cambios(self):
        titular = aliased(PlanLiga)
        # id del registro afectado segun el modulo (compatibilidad con el front).
        registro_id = case(
            (Auditoria.modulo == "beneficiarios", Auditoria.id_beneficiario),
            else_=Auditoria.id_titular,
        ).label("registro_id")
        return select(
            Auditoria,
            registro_id,
            Usuario.usuario.label("login"),
            Usuario.nombres.label("nombres"),
            titular.nombre1.label("t_nombre1"),
            titular.nombre2.label("t_nombre2"),
            titular.apellido1.label("t_apellido1"),
            titular.apellido2.label("t_apellido2"),
            titular.documento.label("t_documento"),
        ).outerjoin(Usuario, Usuario.id == Auditoria.id_usuario).outerjoin(
            titular, titular.id == Auditoria.id_titular
        )

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

    def listar_cambios(
        self, modulos: list[str] | None, desde: datetime | None, hasta: datetime | None
    ) -> list:
        stmt = self._consulta_cambios()
        if modulos:
            stmt = stmt.where(Auditoria.modulo.in_(modulos))
        if desde:
            stmt = stmt.where(Auditoria.fecha_actualizacion >= desde)
        if hasta:
            stmt = stmt.where(Auditoria.fecha_actualizacion < hasta)
        stmt = stmt.order_by(
            Auditoria.fecha_actualizacion.desc(), Auditoria.id.desc()
        ).limit(LIMITE_CAMBIOS + 1)
        return list(self.db.execute(stmt).all())

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
               NULL AS TITULAR_ID, NULL AS T_NOMBRE1, NULL AS T_NOMBRE2, NULL AS T_APELLIDO1, NULL AS T_APELLIDO2
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
               p.ID, p.NOMBRE1, p.NOMBRE2, p.APELLIDO1, p.APELLIDO2
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
