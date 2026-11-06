from datetime import date, datetime, time, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.administracion.auditoria.repository import LIMITE_CAMBIOS, AuditoriaRepository
from app.modules.administracion.auditoria.schemas import (
    Cambio,
    ListadoCambios,
    Renovacion,
    RenovadoPor,
    ResumenModulo,
    TitularGrupo,
    TitularRef,
)

# Colombia no tiene horario de verano: UTC-5 fijo (evita depender de tzdata en Windows).
ZONA_LOCAL = timezone(timedelta(hours=-5))

ESTADOS = {"A": "Activo", "I": "Inactivo"}


def _nombre(*partes: str | None) -> str:
    return " ".join(p.strip() for p in partes if p and p.strip())


def _a_utc_naive(dia: date, fin: bool = False) -> datetime:
    """Limite de un dia LOCAL convertido a UTC (asi se guarda la fecha en la tabla)."""
    if fin:
        dia = dia + timedelta(days=1)
    return datetime.combine(dia, time.min, tzinfo=ZONA_LOCAL).astimezone(timezone.utc).replace(tzinfo=None)


def _fecha_utc(valor: datetime) -> datetime:
    return valor if valor.tzinfo else valor.replace(tzinfo=timezone.utc)


def _solo_fecha(valor) -> date | None:
    if valor is None:
        return None
    return valor.date() if isinstance(valor, datetime) else valor


def _vigencia(fecha_ingreso: date | None, fecha_renovado: date | None) -> date | None:
    base = fecha_renovado or fecha_ingreso
    if base is None:
        return None
    try:
        return base.replace(year=base.year + 1)
    except ValueError:  # 29 de febrero
        return base.replace(year=base.year + 1, day=28)


class AuditoriaService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = AuditoriaRepository(db)
        self._roles: dict[int, str | None] = {}

    def _rol(self, usuario_id: int | None) -> str | None:
        if usuario_id is None:
            return "Sistema"
        if usuario_id not in self._roles:
            from app.modules.auth.repository import AuthRepository

            self._roles[usuario_id] = AuthRepository(self.db).obtener_rol_crm(usuario_id)
        return self._roles[usuario_id]

    def _mapear(self, fila) -> Cambio:
        a = fila.Auditoria
        registro_id = getattr(fila, "registro_id", None)
        if registro_id is None:
            registro_id = a.id_beneficiario if a.modulo == "beneficiarios" else a.id_titular
        registro_id = int(registro_id or 0)
        titular = None
        if a.id_titular is not None:
            titular = TitularGrupo(
                id=a.id_titular,
                nombre=_nombre(fila.t_nombre1, fila.t_nombre2, fila.t_apellido1, fila.t_apellido2)
                or f"Titular {a.id_titular}",
                documento=fila.t_documento,
            )
        fecha_ingreso = _solo_fecha(a.fecha_ingreso)
        fecha_fin = _solo_fecha(a.fecha_fin)
        es_plan_liga = a.modulo in ("titulares", "beneficiarios")
        return Cambio(
            id=a.id,
            fecha=_fecha_utc(a.fecha_actualizacion),
            usuario_id=a.id_usuario or 0,
            usuario=fila.login or "sistema",
            nombre_usuario=fila.nombres or (
                "Proceso automático" if a.id_usuario is None else f"Usuario {a.id_usuario}"
            ),
            rol=self._rol(a.id_usuario),
            ip=None,
            accion=a.accion,
            origen=a.origen,
            lote_id=None,
            modulo=a.modulo,
            registro_id=registro_id,
            registro_nombre=a.registro_nombre or f"Registro {registro_id}",
            documento=a.documento,
            titular=titular,
            id_titular=a.id_titular,
            id_beneficiario=a.id_beneficiario,
            # En la tabla se guarda A / I; el front muestra el texto.
            estado_antes=ESTADOS.get(a.estado_antes, a.estado_antes),
            estado_despues=ESTADOS.get(a.estado_despues, a.estado_despues),
            fecha_inscripcion=_solo_fecha(a.fecha_inscripcion),
            fecha_registro=_solo_fecha(a.fecha_registro),
            fecha_ingreso=fecha_ingreso,
            renovado=(a.renovado == "S") if es_plan_liga and a.renovado else None,
            fecha_renovado=None,
            vigencia_hasta=(fecha_fin or _vigencia(fecha_ingreso, None)) if es_plan_liga else None,
            motivo=None,
            campos=[],
        )

    @staticmethod
    def _rango(desde: date | None, hasta: date | None) -> tuple[datetime | None, datetime | None]:
        return (
            _a_utc_naive(desde) if desde else None,
            _a_utc_naive(hasta, fin=True) if hasta else None,
        )

    def resumen_modulos(self, desde: date | None, hasta: date | None) -> list[ResumenModulo]:
        ini, fin = self._rango(desde, hasta)
        return [
            ResumenModulo(modulo=m, total=t, ultimo_cambio=_fecha_utc(u) if u else None)
            for m, t, u in self.repository.resumen_por_modulo(ini, fin)
        ]

    def listar_cambios(
        self, modulo: str | None, desde: date | None, hasta: date | None
    ) -> ListadoCambios:
        modulos = [m.strip() for m in modulo.split(",") if m.strip()] if modulo else None
        ini, fin = self._rango(desde, hasta)
        filas = self.repository.listar_cambios(modulos, ini, fin)
        truncado = len(filas) > LIMITE_CAMBIOS
        items = [self._mapear(f) for f in filas[:LIMITE_CAMBIOS]]
        return ListadoCambios(items=items, total=len(items), truncado=truncado)

    def obtener_cambio(self, id_cambio: int) -> Cambio:
        fila = self.repository.obtener_cambio(id_cambio)
        if fila is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontró el cambio.")
        return self._mapear(fila)

    def historial(self, modulo: str, registro_id: int) -> list[Cambio]:
        return [self._mapear(f) for f in self.repository.historial(modulo, registro_id)]

    def renovaciones(self, tipo: str | None) -> list[Renovacion]:
        ultimas = self.repository.ultimas_renovaciones()
        resultado: list[Renovacion] = []
        for f in self.repository.listar_renovaciones(tipo):
            modulo = "titulares" if f["tipo"] == "titular" else "beneficiarios"
            por = ultimas.get((modulo, int(f["id"])))
            titular = None
            if f.get("titular_id") is not None:
                titular = TitularRef(
                    id=int(f["titular_id"]),
                    nombre=_nombre(f["t_nombre1"], f["t_nombre2"], f["t_apellido1"], f["t_apellido2"]),
                )
            resultado.append(
                Renovacion(
                    tipo=f["tipo"],
                    id=int(f["id"]),
                    nombre=_nombre(f["nombre1"], f["nombre2"], f["apellido1"], f["apellido2"]),
                    documento=f["documento"] or "",
                    empresa=f["empresa"],
                    plan=f["plan"],
                    estado=ESTADOS.get(f["estado"], f["estado"] or ""),
                    fecha_ingreso=_solo_fecha(f["fecha_ingreso"]),
                    renovado=f["renovado"] == "S",
                    fecha_renovado=_solo_fecha(f["fecha_renovado"]),
                    vencimiento=_solo_fecha(f["vencimiento"]),
                    renovado_por=RenovadoPor(nombre=por[0] or por[1] or "", usuario=por[1] or "")
                    if por and f["renovado"] == "S"
                    else None,
                    titular=titular,
                )
            )
        return resultado
