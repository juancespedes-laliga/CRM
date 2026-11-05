from datetime import datetime

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session, aliased

from app.models import Auditoria, PlanLiga, Usuario

# Tope de filas por consulta del log: el front filtra en memoria lo que llega.
LIMITE_CAMBIOS = 5000


class AuditoriaRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _consulta_cambios(self):
        titular = aliased(PlanLiga)
        return select(
            Auditoria,
            Usuario.usuario.label("login"),
            Usuario.nombres.label("nombres"),
            titular.nombre1.label("t_nombre1"),
            titular.nombre2.label("t_nombre2"),
            titular.apellido1.label("t_apellido1"),
            titular.apellido2.label("t_apellido2"),
            titular.documento.label("t_documento"),
        ).outerjoin(Usuario, Usuario.id == Auditoria.usuario_id).outerjoin(
            titular, titular.id == Auditoria.titular_id
        )

    def resumen_por_modulo(
        self, desde: datetime | None, hasta: datetime | None
    ) -> list[tuple[str, int, datetime | None]]:
        stmt = select(Auditoria.modulo, func.count(), func.max(Auditoria.fecha)).group_by(
            Auditoria.modulo
        )
        if desde:
            stmt = stmt.where(Auditoria.fecha >= desde)
        if hasta:
            stmt = stmt.where(Auditoria.fecha < hasta)
        return [tuple(f) for f in self.db.execute(stmt).all()]

    def listar_cambios(
        self, modulos: list[str] | None, desde: datetime | None, hasta: datetime | None
    ) -> list:
        stmt = self._consulta_cambios()
        if modulos:
            stmt = stmt.where(Auditoria.modulo.in_(modulos))
        if desde:
            stmt = stmt.where(Auditoria.fecha >= desde)
        if hasta:
            stmt = stmt.where(Auditoria.fecha < hasta)
        stmt = stmt.order_by(Auditoria.fecha.desc(), Auditoria.id.desc()).limit(LIMITE_CAMBIOS + 1)
        return list(self.db.execute(stmt).all())

    def obtener_cambio(self, id_cambio: int):
        stmt = self._consulta_cambios().where(Auditoria.id == id_cambio)
        return self.db.execute(stmt).first()

    def historial(self, modulo: str, registro_id: int) -> list:
        stmt = (
            self._consulta_cambios()
            .where(Auditoria.modulo == modulo, Auditoria.registro_id == registro_id)
            .order_by(Auditoria.fecha.desc(), Auditoria.id.desc())
        )
        return list(self.db.execute(stmt).all())

    def ultimas_renovaciones(self) -> dict[tuple[str, int], tuple[str | None, str | None]]:
        """(modulo, registro_id) -> (nombre, login) de quien hizo la ultima renovacion."""
        stmt = (
            select(Auditoria.modulo, Auditoria.registro_id, Usuario.nombres, Usuario.usuario)
            .outerjoin(Usuario, Usuario.id == Auditoria.usuario_id)
            .where(
                Auditoria.modulo.in_(["titulares", "beneficiarios"]),
                Auditoria.accion.in_(["renovacion", "activacion"]),
                Auditoria.renovado == "S",
            )
            .order_by(Auditoria.fecha.desc(), Auditoria.id.desc())
        )
        resultado: dict[tuple[str, int], tuple[str | None, str | None]] = {}
        for modulo, registro_id, nombres, login in self.db.execute(stmt).all():
            resultado.setdefault((modulo, registro_id), (nombres, login))
        return resultado

    # Titulares y beneficiarios con fecha de ingreso. Vencimiento = un anio
    # despues de la ultima renovacion (o del ingreso si nunca ha renovado):
    # misma regla que Renovaciones por mes (ver titulares_beneficiarios/repository.py).
    _SQL_RENOVACIONES = """
        SELECT 'titular' AS TIPO, p.ID, p.NOMBRE1, p.NOMBRE2, p.APELLIDO1, p.APELLIDO2,
               p.DOCUMENTO, p.EMPRESA,
               NVL(tp.NOMBRE || CASE WHEN tp.CATEGORIA IS NOT NULL THEN ' - ' || tp.CATEGORIA END, p.TIPO_PLAN) AS PLAN,
               p.ESTADO, TRUNC(p.FECHA_INGRESO) AS FECHA_INGRESO, p.RENOVADO,
               TRUNC(p.FECHA_RENOVADO) AS FECHA_RENOVADO,
               TRUNC(ADD_MONTHS(NVL(p.FECHA_RENOVADO, p.FECHA_INGRESO), 12)) AS VENCIMIENTO,
               NULL AS TITULAR_ID, NULL AS T_NOMBRE1, NULL AS T_NOMBRE2, NULL AS T_APELLIDO1, NULL AS T_APELLIDO2
        FROM INTRANET_PLANLIGA p
        LEFT JOIN INTRANET_PLANLIGA_TIPO_PLAN tp ON tp.ID = p.TIPO_PLAN_ID
        WHERE p.FECHA_INGRESO IS NOT NULL {filtro_t}
        UNION ALL
        SELECT 'beneficiario', b.ID, b.NOMBRE1, b.NOMBRE2, b.APELLIDO1, b.APELLIDO2,
               b.DOCUMENTO, NVL(b.EMPRESA, p.EMPRESA),
               NVL(tp.NOMBRE || CASE WHEN tp.CATEGORIA IS NOT NULL THEN ' - ' || tp.CATEGORIA END,
                   NVL(TRIM(b.TIPO_PLAN), p.TIPO_PLAN)),
               b.ESTADO, TRUNC(b.FECHA_INGRESO), b.RENOVADO, TRUNC(b.FECHA_RENOVADO),
               TRUNC(ADD_MONTHS(NVL(b.FECHA_RENOVADO, b.FECHA_INGRESO), 12)),
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
        # Claves en minuscula sin importar como las devuelva el driver.
        return [
            {k.lower(): v for k, v in f.items()}
            for f in self.db.execute(text(sql)).mappings().all()
        ]
