"""Escritura en mercadeo_crm_auditoria, para usar desde los services de cada modulo.

Es best-effort: la accion principal ya hizo commit cuando se registra la
auditoria, asi que si guardarla falla se loguea el error y NO se tumba la
operacion del usuario.

Uso:
    auditor = RegistradorAuditoria(db, contexto)
    auditor.registrar(modulo="titulares", accion="edicion", id_titular=10, ...)
"""

import logging
from datetime import date, datetime
from typing import Any

from sqlalchemy import insert, select
from sqlalchemy.orm import Session

from app.models import Auditoria, Usuario
from app.modules.administracion.auditoria.contexto import ContextoAuditoria

logger = logging.getLogger(__name__)

ACCIONES = {
    "creacion", "edicion", "activacion", "desactivacion", "renovacion",
    "cambio_plan", "cambio_titular", "reemplazo", "eliminacion",
}


def campo_cambiado(campo: str, etiqueta: str, antes: Any, despues: Any) -> dict:
    return {"campo": campo, "etiqueta": etiqueta, "antes": _texto(antes), "despues": _texto(despues)}


def _texto(valor: Any) -> str | None:
    if valor is None or valor == "":
        return None
    if isinstance(valor, (date, datetime)):
        return valor.isoformat()
    return str(valor)


class RegistradorAuditoria:
    def __init__(self, db: Session, contexto: ContextoAuditoria | None) -> None:
        self.db = db
        self.contexto = contexto
        self._usuario_id: int | None = None
        self._usuario_resuelto = False

    def _usuario(self) -> int | None:
        if not self._usuario_resuelto:
            self._usuario_resuelto = True
            username = self.contexto.username if self.contexto else None
            if username:
                self._usuario_id = self.db.scalar(
                    select(Usuario.id).where(Usuario.usuario == username)
                )
        return self._usuario_id

    def fila(
        self,
        *,
        modulo: str,
        accion: str,
        registro_nombre: str | None = None,
        documento: str | None = None,
        id_titular: int | None = None,
        id_beneficiario: int | None = None,
        estado_antes: str | None = None,
        estado_despues: str | None = None,
        fecha_inscripcion: date | None = None,
        fecha_registro: date | None = None,
        fecha_ingreso: date | None = None,
        renovado: str | None = None,
        origen: str | None = None,
    ) -> dict:
        """Arma una fila lista para insertar (sin escribirla todavia).

        No manda id ni fecha_actualizacion: los pone el trigger de Oracle.
        No manda fecha_fin: es columna virtual.
        fecha_inscripcion solo debe venir en altas nuevas.
        """
        if accion not in ACCIONES:
            raise ValueError(f"Accion de auditoria desconocida: {accion}")
        ctx = self.contexto
        return {
            "id_usuario": self._usuario(),
            "modulo": modulo,
            "accion": accion,
            "origen": "sistema" if ctx is None
            else (ctx.origen if ctx.origen != "manual" else origen) or "manual",
            "registro_nombre": (registro_nombre or None) and registro_nombre[:150],
            "documento": (documento or None) and str(documento)[:20],
            "id_titular": id_titular,
            "id_beneficiario": id_beneficiario,
            "estado_antes": estado_antes,
            "estado_despues": estado_despues,
            "fecha_inscripcion": fecha_inscripcion,
            "fecha_registro": fecha_registro,
            "fecha_ingreso": fecha_ingreso,
            "renovado": renovado,
        }

    def registrar(self, **datos: Any) -> None:
        self.registrar_varios([self.fila(**datos)])

    def registrar_varios(self, filas: list[dict]) -> None:
        if not filas:
            return
        try:
            self.db.execute(insert(Auditoria), filas)
            self.db.commit()
        except Exception:
            self.db.rollback()
            logger.exception(
                "No se pudo registrar la auditoria (%s filas, modulo=%s, accion=%s)",
                len(filas), filas[0].get("modulo"), filas[0].get("accion"),
            )
