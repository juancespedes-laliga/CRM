from datetime import date, datetime

from sqlalchemy import text
from sqlalchemy.orm import Session

from .schemas import AudienciaSegmentoItem

# Consolidado de marketing: servicios clinicos (TMPBI1) cruzados con
# afiliados activos de Plan Liga (INTRANET_VISTA_PLANLIGA). Una fila por
# persona (RN=1 = ultimo servicio). Sin ORDER BY/paginacion: eso se agrega
# en _ejecutar_pagina/_contar segun haga falta (ver mas abajo).
#
# El total de personas que devuelve esto NO va a coincidir con un
# `SELECT COUNT(*) FROM TMPBI1 WHERE TARIFA = 'PL'` directo: esa cuenta
# filas (TMPBI1 es un log de servicios, una persona puede tener varias),
# mientras que aca se colapsa a 1 fila por persona (RN=1) y ademas se exige
# que este activa en Plan Liga (INNER JOIN + p.ESTADO = 'A'). Es esperado
# que el numero de personas termine bastante mas bajo que el de filas.
_SQL_AUDIENCIA = """
SELECT
    IDENTIFICACION,
    NOMBRES,
    EMPRESA,
    SEXO,
    EDAD,
    CIUDAD,
    DEPARTAMENTO,
    CORREO,
    TELEFONO,
    TIPO_PLAN,
    CONCEPTO,
    SERVICIO,
    ESPECIALIDAD,
    SERVICIOS_USADOS,
    ULTIMO_USO,
    TIPO_VINCULACION
FROM (
    SELECT
        t.IDENTIFICACION,
        t.NOMBRES,
        t.EMPRESA,
        t.SEXO,
        t.EDAD,
        t.MUNICIPIO AS CIUDAD,
        t.DEPARTAMENTO,
        t.PACCOE AS CORREO,
        t.PACCEL AS TELEFONO,
        p.TIPO_PLAN,
        t.CONCEPTO,
        t.SERVICIO,
        t.ESPECIALIDAD,
        COUNT(*) OVER (PARTITION BY t.IDENTIFICACION) AS SERVICIOS_USADOS,
        MAX(t.FECHA) OVER (PARTITION BY t.IDENTIFICACION) AS ULTIMO_USO,
        CASE
            WHEN UPPER(p.TIPO_PLAN) = 'PARTICULAR' THEN 'Particular'
            ELSE 'Empresa'
        END AS TIPO_VINCULACION,
        ROW_NUMBER() OVER (
            PARTITION BY t.IDENTIFICACION
            ORDER BY t.FECHA DESC
        ) AS RN
    FROM TMPBI1 t
    INNER JOIN (
        SELECT DISTINCT DOCUMENTO, ESTADO, TIPO_PLAN
        FROM INTRANET_VISTA_PLANLIGA
    ) p
        ON p.DOCUMENTO = t.IDENTIFICACION
    -- TARIFA = 'PL' va primero (antes que el resto de filtros) por lo mismo
    -- que en _SQL_AUDIENCIA_NO_PLAN_LIGA: TMPBI1 tiene ~5 millones de filas,
    -- asi que conviene reducirla con esta condicion antes de evaluar el
    -- resto (igual que p.ESTADO = 'A' y los filtros opcionales de abajo).
    WHERE t.TARIFA = 'PL'
      AND p.ESTADO = 'A'
      AND (:sexo IS NULL OR UPPER(t.SEXO) = UPPER(:sexo))
      AND (:edad_min IS NULL OR t.EDAD >= :edad_min)
      AND (:edad_max IS NULL OR t.EDAD <= :edad_max)
      AND (:ciudad IS NULL OR UPPER(TRIM(t.MUNICIPIO)) = UPPER(:ciudad))
      AND (:departamento IS NULL OR UPPER(TRIM(t.DEPARTAMENTO)) = UPPER(:departamento))
      AND (:concepto IS NULL OR UPPER(TRIM(t.CONCEPTO)) = UPPER(:concepto))
      AND (:servicio IS NULL OR UPPER(TRIM(t.SERVICIO)) = UPPER(:servicio))
      AND (
            :tipo_vinculacion IS NULL
            OR (UPPER(:tipo_vinculacion) = 'PARTICULAR' AND UPPER(p.TIPO_PLAN) = 'PARTICULAR')
            OR (
                UPPER(:tipo_vinculacion) = 'EMPRESA'
                AND (p.TIPO_PLAN IS NULL OR UPPER(p.TIPO_PLAN) != 'PARTICULAR')
            )
      )
)
WHERE RN = 1
  AND (
        :ultimo_uso IS NULL
        OR (:ultimo_uso = '90' AND ULTIMO_USO <= SYSDATE - 90)
        OR (:ultimo_uso = '60' AND ULTIMO_USO <= SYSDATE - 60)
        OR (:ultimo_uso = '30' AND ULTIMO_USO <= SYSDATE - 30)
  )
"""

# Consolidado "no Plan Liga": mismo cruce con TMPBI1, pero la audiencia
# sale de ABPAC (personas con historia clinica/usuario Servinte, campo
# PACIDE = cedula) EXCLUYENDO a quienes son afiliados ACTIVOS de Plan Liga
# (INTRANET_VISTA_PLANLIGA.ESTADO = 'A'). Un inactivo de Plan Liga si cae
# en esta audiencia.
#
# IMPORTANTE (rendimiento): el filtrado de TMPBI1 (concepto/servicio/sexo/etc)
# va primero en el WHERE y el INNER JOIN a ABPAC + el NOT EXISTS contra
# INTRANET_VISTA_PLANLIGA se evaluan por cada fila de TMPBI1 ya filtrada, NO
# sobre toda la tabla ABPAC completa (esa version anterior escaneaba ABPAC
# entero antes de aplicar cualquier filtro y quedaba colgada).
_SQL_AUDIENCIA_NO_PLAN_LIGA = """
SELECT
    IDENTIFICACION,
    NOMBRES,
    EMPRESA,
    SEXO,
    EDAD,
    CIUDAD,
    DEPARTAMENTO,
    CORREO,
    TELEFONO,
    TIPO_PLAN,
    CONCEPTO,
    SERVICIO,
    ESPECIALIDAD,
    SERVICIOS_USADOS,
    ULTIMO_USO,
    TIPO_VINCULACION
FROM (
    SELECT
        t.IDENTIFICACION,
        t.NOMBRES,
        t.EMPRESA,
        t.SEXO,
        t.EDAD,
        t.MUNICIPIO AS CIUDAD,
        t.DEPARTAMENTO,
        t.PACCOE AS CORREO,
        t.PACCEL AS TELEFONO,
        t.TIPO_PLAN,
        t.CONCEPTO,
        t.SERVICIO,
        t.ESPECIALIDAD,
        COUNT(*) OVER (PARTITION BY t.IDENTIFICACION) AS SERVICIOS_USADOS,
        MAX(t.FECHA) OVER (PARTITION BY t.IDENTIFICACION) AS ULTIMO_USO,
        CASE
            WHEN UPPER(t.TIPO_PLAN) = 'PARTICULAR' THEN 'Particular'
            ELSE 'Empresa'
        END AS TIPO_VINCULACION,
        ROW_NUMBER() OVER (
            PARTITION BY t.IDENTIFICACION
            ORDER BY t.FECHA DESC
        ) AS RN
    FROM TMPBI1 t
    INNER JOIN ABPAC a
        ON a.PACIDE = t.IDENTIFICACION
    WHERE NOT EXISTS (
            SELECT 1
            FROM INTRANET_VISTA_PLANLIGA p
            WHERE p.DOCUMENTO = t.IDENTIFICACION
              AND p.ESTADO = 'A'
      )
      AND (:sexo IS NULL OR UPPER(t.SEXO) = UPPER(:sexo))
      AND (:edad_min IS NULL OR t.EDAD >= :edad_min)
      AND (:edad_max IS NULL OR t.EDAD <= :edad_max)
      AND (:ciudad IS NULL OR UPPER(TRIM(t.MUNICIPIO)) = UPPER(:ciudad))
      AND (:departamento IS NULL OR UPPER(TRIM(t.DEPARTAMENTO)) = UPPER(:departamento))
      AND (:concepto IS NULL OR UPPER(TRIM(t.CONCEPTO)) = UPPER(:concepto))
      AND (:servicio IS NULL OR UPPER(TRIM(t.SERVICIO)) = UPPER(:servicio))
      AND (
            :tipo_vinculacion IS NULL
            OR (UPPER(:tipo_vinculacion) = 'PARTICULAR' AND UPPER(t.TIPO_PLAN) = 'PARTICULAR')
            OR (
                UPPER(:tipo_vinculacion) = 'EMPRESA'
                AND (t.TIPO_PLAN IS NULL OR UPPER(t.TIPO_PLAN) != 'PARTICULAR')
            )
      )
)
WHERE RN = 1
  AND (
        :ultimo_uso IS NULL
        OR (:ultimo_uso = '90' AND ULTIMO_USO <= SYSDATE - 90)
        OR (:ultimo_uso = '60' AND ULTIMO_USO <= SYSDATE - 60)
        OR (:ultimo_uso = '30' AND ULTIMO_USO <= SYSDATE - 30)
  )
"""

# Audiencia "sin uso": titulares/beneficiarios ACTIVOS (INTRANET_PLANLIGA /
# INTRANET_PLANLIGA_BENEFICIARIO, no la vista) que NO tienen ningun servicio
# con TARIFA = 'PL' en TMPBI1 -- lo opuesto de _SQL_AUDIENCIA, que sale DE
# TMPBI1 y por construccion solo puede traer gente que si tiene servicios ahi.
# Sin fila en TMPBI1 no hay CONCEPTO/SERVICIO/ESPECIALIDAD/ULTIMO_USO que
# mostrar (quedan NULL) ni forma de filtrar por esas columnas ni por
# ultimo_uso -- si el frontend los manda igual, simplemente no hacen nada
# (no estan referenciados en este SQL).
_SQL_AUDIENCIA_SIN_USO = """
SELECT
    IDENTIFICACION,
    NOMBRES,
    EMPRESA,
    SEXO,
    EDAD,
    CIUDAD,
    DEPARTAMENTO,
    CORREO,
    TELEFONO,
    TIPO_PLAN,
    CAST(NULL AS VARCHAR2(200)) AS CONCEPTO,
    CAST(NULL AS VARCHAR2(200)) AS SERVICIO,
    CAST(NULL AS VARCHAR2(200)) AS ESPECIALIDAD,
    0 AS SERVICIOS_USADOS,
    CAST(NULL AS DATE) AS ULTIMO_USO,
    TIPO_VINCULACION
FROM (
    -- CIUDAD/DEPARTAMENTO en INTRANET_PLANLIGA/_BENEFICIARIO guardan el
    -- CODIGO Divipola (MUNCOD/DEPCOD), no el nombre -- a diferencia de
    -- TMPBI1.MUNICIPIO/DEPARTAMENTO, que si traen el nombre directo. Sin
    -- este cruce con INMUN/INDEP (mismos catalogos del modulo de
    -- ubicaciones, ver compartidos/ubicaciones/repository.py) esta columna
    -- mostraba el codigo numerico en vez del nombre.
    SELECT
        p.DOCUMENTO AS IDENTIFICACION,
        REGEXP_REPLACE(
            p.NOMBRE1 || ' ' || NVL(p.NOMBRE2, '') || ' ' || p.APELLIDO1 || ' ' || NVL(p.APELLIDO2, ''),
            ' +', ' '
        ) AS NOMBRES,
        p.EMPRESA,
        p.SEXO,
        TRUNC(MONTHS_BETWEEN(SYSDATE, p.FECHA_NACIMIENTO) / 12) AS EDAD,
        -- No sabemos con certeza si CIUDAD guarda el codigo corto de INMUN
        -- (unico solo junto con el departamento) o el codigo Divipola
        -- completo (departamento+municipio concatenado): se prueban ambas
        -- formas, y si ninguna matchea se deja el valor tal cual (mejor
        -- mostrar el codigo crudo que dejarlo en blanco).
        COALESCE(UPPER(TRIM(m.MUNNOM)), UPPER(TRIM(p.CIUDAD))) AS CIUDAD,
        COALESCE(UPPER(TRIM(d.DEPNOM)), UPPER(TRIM(p.DEPARTAMENTO))) AS DEPARTAMENTO,
        p.CORREO,
        p.TELEFONO,
        p.TIPO_PLAN,
        CASE WHEN UPPER(p.TIPO_PLAN) = 'PARTICULAR' THEN 'Particular' ELSE 'Empresa' END AS TIPO_VINCULACION
    FROM INTRANET_PLANLIGA p
    LEFT JOIN INMUN m
        ON (m.MUNCOD = p.CIUDAD AND m.MUNDEP = p.DEPARTAMENTO)
        OR (m.MUNDEP || m.MUNCOD = p.CIUDAD)
    LEFT JOIN INDEP d ON d.DEPCOD = p.DEPARTAMENTO
    WHERE p.ESTADO = 'A'
      AND NOT EXISTS (
          SELECT 1 FROM TMPBI1 b WHERE b.IDENTIFICACION = p.DOCUMENTO AND b.TARIFA = 'PL'
      )

    UNION ALL

    SELECT
        ben.DOCUMENTO AS IDENTIFICACION,
        REGEXP_REPLACE(
            ben.NOMBRE1 || ' ' || NVL(ben.NOMBRE2, '') || ' ' || ben.APELLIDO1 || ' ' || NVL(ben.APELLIDO2, ''),
            ' +', ' '
        ) AS NOMBRES,
        ben.EMPRESA,
        ben.SEXO,
        TRUNC(MONTHS_BETWEEN(SYSDATE, ben.FECHA_NACIMIENTO) / 12) AS EDAD,
        COALESCE(UPPER(TRIM(m2.MUNNOM)), UPPER(TRIM(ben.CIUDAD))) AS CIUDAD,
        COALESCE(UPPER(TRIM(d2.DEPNOM)), UPPER(TRIM(ben.DEPARTAMENTO))) AS DEPARTAMENTO,
        ben.CORREO,
        ben.TELEFONO,
        ben.TIPO_PLAN,
        CASE WHEN UPPER(ben.TIPO_PLAN) = 'PARTICULAR' THEN 'Particular' ELSE 'Empresa' END AS TIPO_VINCULACION
    FROM INTRANET_PLANLIGA_BENEFICIARIO ben
    LEFT JOIN INMUN m2
        ON (m2.MUNCOD = ben.CIUDAD AND m2.MUNDEP = ben.DEPARTAMENTO)
        OR (m2.MUNDEP || m2.MUNCOD = ben.CIUDAD)
    LEFT JOIN INDEP d2 ON d2.DEPCOD = ben.DEPARTAMENTO
    WHERE ben.ESTADO = 'A'
      AND NOT EXISTS (
          SELECT 1 FROM TMPBI1 t WHERE t.IDENTIFICACION = ben.DOCUMENTO AND t.TARIFA = 'PL'
      )
)
WHERE (:sexo IS NULL OR UPPER(SEXO) = UPPER(:sexo))
  AND (:edad_min IS NULL OR EDAD >= :edad_min)
  AND (:edad_max IS NULL OR EDAD <= :edad_max)
  AND (:ciudad IS NULL OR CIUDAD = UPPER(:ciudad))
  AND (:departamento IS NULL OR DEPARTAMENTO = UPPER(:departamento))
  AND (
        :tipo_vinculacion IS NULL
        OR (UPPER(:tipo_vinculacion) = 'PARTICULAR' AND UPPER(TIPO_PLAN) = 'PARTICULAR')
        OR (
            UPPER(:tipo_vinculacion) = 'EMPRESA'
            AND (TIPO_PLAN IS NULL OR UPPER(TIPO_PLAN) != 'PARTICULAR')
        )
  )
"""

# Audiencia "todos" de Plan Liga: los que han usado el plan (_SQL_AUDIENCIA) MAS
# los que no (_SQL_AUDIENCIA_SIN_USO). Las dos devuelven las mismas columnas en
# el mismo orden y no se cruzan entre si (una exige servicio con TARIFA = 'PL' en
# TMPBI1 y la otra exige NO tenerlo), asi que UNION ALL no duplica personas. El
# ORDER BY ULTIMO_USO DESC NULLS LAST de _SQL_PAGINA deja primero a los que han
# usado el plan y al final a los que no (ULTIMO_USO = NULL).
_SQL_AUDIENCIA_TODOS = f"""
SELECT * FROM (
{_SQL_AUDIENCIA}
)
UNION ALL
SELECT * FROM (
{_SQL_AUDIENCIA_SIN_USO}
)
"""

# COUNT(*) OVER() (sin PARTITION BY) calcula el total de filas que cumplen
# el filtro ANTES de recortar con OFFSET/FETCH -- Oracle evalua las funciones
# de ventana sobre el resultado completo y recien al final aplica el recorte
# de pagina, asi que el total sale correcto en la MISMA pasada, sin repetir
# el join+ventanas caros de sql_base con una segunda consulta de COUNT(*).
_SQL_PAGINA = """
SELECT x.*, COUNT(*) OVER () AS TOTAL_FILAS
FROM (
    {base}
) x
ORDER BY x.ULTIMO_USO DESC NULLS LAST
OFFSET :offset ROWS FETCH NEXT :limite ROWS ONLY
"""

# Valores distintos para poblar los desplegables de filtro (ciudad, concepto,
# servicio). TMPBI1 tiene ~5 millones de filas, asi que esto tambien puede
# ser lento -- el service lo cachea en memoria para no pegarle a la tabla
# en cada carga del panel de filtros (ver SegmentosService).
_SQL_VALORES_MUNICIPIO = """
SELECT DISTINCT UPPER(TRIM(MUNICIPIO)) AS VALOR
FROM TMPBI1
WHERE TRIM(MUNICIPIO) IS NOT NULL
ORDER BY VALOR
"""

_SQL_VALORES_CONCEPTO = """
SELECT DISTINCT UPPER(TRIM(CONCEPTO)) AS VALOR
FROM TMPBI1
WHERE TRIM(CONCEPTO) IS NOT NULL
ORDER BY VALOR
"""

_SQL_VALORES_SERVICIO = """
SELECT DISTINCT UPPER(TRIM(SERVICIO)) AS VALOR
FROM TMPBI1
WHERE TRIM(SERVICIO) IS NOT NULL
ORDER BY VALOR
"""

# Pares (departamento, municipio) distintos, para el desplegable en cascada:
# primero elige departamento, y el de municipio se filtra a los que
# pertenecen a ese departamento (todo se trae una sola vez y se filtra en
# el frontend, en vez de volver a consultar TMPBI1 por cada departamento).
_SQL_UBICACIONES = """
SELECT DISTINCT
    UPPER(TRIM(DEPARTAMENTO)) AS DEPARTAMENTO,
    UPPER(TRIM(MUNICIPIO)) AS MUNICIPIO
FROM TMPBI1
WHERE TRIM(DEPARTAMENTO) IS NOT NULL
  AND TRIM(MUNICIPIO) IS NOT NULL
ORDER BY DEPARTAMENTO, MUNICIPIO
"""

# Pares (concepto, servicio) distintos, para el mismo patron en cascada:
# primero elige concepto, y el desplegable de servicio se filtra a los
# servicios que realmente pertenecen a ese concepto en TMPBI1 (antes el
# desplegable de servicio mostraba TODOS los servicios sin importar el
# concepto elegido).
_SQL_CONCEPTOS_SERVICIOS = """
SELECT DISTINCT
    UPPER(TRIM(CONCEPTO)) AS CONCEPTO,
    UPPER(TRIM(SERVICIO)) AS SERVICIO
FROM TMPBI1
WHERE TRIM(CONCEPTO) IS NOT NULL
  AND TRIM(SERVICIO) IS NOT NULL
ORDER BY CONCEPTO, SERVICIO
"""


# ---------------------------------------------------------------------------
# Uso de Plan Liga: cuantos titulares/beneficiarios ACTIVOS (segun sus propias
# tablas, INTRANET_PLANLIGA / INTRANET_PLANLIGA_BENEFICIARIO) tienen al menos
# un servicio con TARIFA = 'PL' en TMPBI1. Se usan estas tablas en vez de
# INTRANET_VISTA_PLANLIGA (la que arma /audiencias) porque necesitamos poder
# separar titulares de beneficiarios, y no conocemos con certeza si esa vista
# distingue entre ambos -- estas dos tablas si tienen esquema propio conocido
# (son las mismas que usa el modulo integraciones/titulares_beneficiarios).
# ---------------------------------------------------------------------------
_SQL_RESUMEN_USO_PLAN = """
SELECT
    (SELECT COUNT(*) FROM INTRANET_PLANLIGA WHERE ESTADO = 'A') AS TITULARES_ACTIVOS,
    (SELECT COUNT(*)
     FROM INTRANET_PLANLIGA t
     WHERE t.ESTADO = 'A'
       AND EXISTS (
           SELECT 1 FROM TMPBI1 b
           WHERE b.IDENTIFICACION = t.DOCUMENTO AND b.TARIFA = 'PL'
       )
    ) AS TITULARES_CON_USO,
    (SELECT COUNT(*) FROM INTRANET_PLANLIGA_BENEFICIARIO WHERE ESTADO = 'A') AS BENEFICIARIOS_ACTIVOS,
    (SELECT COUNT(*)
     FROM INTRANET_PLANLIGA_BENEFICIARIO t
     WHERE t.ESTADO = 'A'
       AND EXISTS (
           SELECT 1 FROM TMPBI1 b
           WHERE b.IDENTIFICACION = t.DOCUMENTO AND b.TARIFA = 'PL'
       )
    ) AS BENEFICIARIOS_CON_USO
FROM DUAL
"""

# Busqueda por documento: primero titular, si no aparece, beneficiario (mismo
# orden que existe_documento() en titulares_beneficiarios/repository.py).
# ORDER BY FECHA_REGISTRO DESC + FETCH FIRST 1: si el documento tiene mas de
# una fila (ej. reemplazos historicos), se toma la mas reciente.
_SQL_BUSCAR_TITULAR_USO = """
SELECT
    DOCUMENTO,
    REGEXP_REPLACE(
        NOMBRE1 || ' ' || NVL(NOMBRE2, '') || ' ' || APELLIDO1 || ' ' || NVL(APELLIDO2, ''),
        ' +', ' '
    ) AS NOMBRE,
    ESTADO
FROM INTRANET_PLANLIGA
WHERE DOCUMENTO = :documento
ORDER BY FECHA_REGISTRO DESC
FETCH FIRST 1 ROWS ONLY
"""

_SQL_BUSCAR_BENEFICIARIO_USO = """
SELECT
    DOCUMENTO,
    REGEXP_REPLACE(
        NOMBRE1 || ' ' || NVL(NOMBRE2, '') || ' ' || APELLIDO1 || ' ' || NVL(APELLIDO2, ''),
        ' +', ' '
    ) AS NOMBRE,
    ESTADO
FROM INTRANET_PLANLIGA_BENEFICIARIO
WHERE DOCUMENTO = :documento
ORDER BY FECHA_REGISTRO DESC
FETCH FIRST 1 ROWS ONLY
"""

_SQL_USO_TMPBI1_POR_DOCUMENTO = """
SELECT
    COUNT(*) AS SERVICIOS_USADOS,
    MAX(FECHA) AS ULTIMO_USO
FROM TMPBI1
WHERE IDENTIFICACION = :documento
  AND TARIFA = 'PL'
"""


def _fecha_iso(valor) -> str | None:
    if valor is None:
        return None
    if isinstance(valor, datetime):
        return valor.date().isoformat()
    if isinstance(valor, date):
        return valor.isoformat()
    return str(valor)


class SegmentosRepository:
    """Consulta el consolidado TMPBI1 para el segmentador de campanas."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def _mapear(self, filas) -> tuple[list[AudienciaSegmentoItem], int]:
        items: list[AudienciaSegmentoItem] = []
        total = 0
        for fila in filas:
            datos = {clave.upper(): valor for clave, valor in fila.items()}
            datos.pop("RN", None)
            total = int(datos.pop("TOTAL_FILAS", 0) or 0)
            if "ULTIMO_USO" in datos:
                datos["ULTIMO_USO"] = _fecha_iso(datos["ULTIMO_USO"])
            if datos.get("EDAD") is not None:
                datos["EDAD"] = int(datos["EDAD"])
            if datos.get("SERVICIOS_USADOS") is not None:
                datos["SERVICIOS_USADOS"] = int(datos["SERVICIOS_USADOS"])
            items.append(AudienciaSegmentoItem(**datos))
        return items, total

    def _ejecutar_pagina(
        self, sql_base: str, params: dict, pagina: int, por_pagina: int
    ) -> tuple[list[AudienciaSegmentoItem], int]:
        """Una sola consulta: trae la pagina pedida y, en la misma pasada,
        el total real via COUNT(*) OVER() (ver _SQL_PAGINA). Si la pagina
        pedida queda vacia (ultima pagina mas alla del total, o sin
        resultados), el total tambien se pierde -- para eso, si la pagina
        pedida no es la primera, se repite solo el conteo (mucho mas barato
        que repetir sql_base+pagina) para no reportar total=0 por error."""
        offset = (pagina - 1) * por_pagina
        params_pagina = {**params, "offset": offset, "limite": por_pagina}
        sql = _SQL_PAGINA.format(base=sql_base)
        filas = self.db.execute(text(sql), params_pagina).mappings().all()
        items, total = self._mapear(filas)

        if not items and pagina > 1:
            total = self.db.scalar(text(f"SELECT COUNT(*) FROM ({sql_base})"), params) or 0

        return items, total

    def listar_audiencia(
        self,
        sexo: str | None = None,
        edad_min: int | None = None,
        edad_max: int | None = None,
        ciudad: str | None = None,
        departamento: str | None = None,
        concepto: str | None = None,
        servicio: str | None = None,
        tipo_vinculacion: str | None = None,
        ultimo_uso: str | None = None,
        pagina: int = 1,
        por_pagina: int = 10,
    ) -> tuple[list[AudienciaSegmentoItem], int]:
        params = {
            "sexo": sexo,
            "edad_min": edad_min,
            "edad_max": edad_max,
            "ciudad": ciudad,
            "departamento": departamento,
            "concepto": concepto,
            "servicio": servicio,
            "tipo_vinculacion": tipo_vinculacion,
            "ultimo_uso": ultimo_uso,
        }
        return self._ejecutar_pagina(_SQL_AUDIENCIA, params, pagina, por_pagina)

    def listar_audiencia_no_plan_liga(
        self,
        sexo: str | None = None,
        edad_min: int | None = None,
        edad_max: int | None = None,
        ciudad: str | None = None,
        departamento: str | None = None,
        concepto: str | None = None,
        servicio: str | None = None,
        tipo_vinculacion: str | None = None,
        ultimo_uso: str | None = None,
        pagina: int = 1,
        por_pagina: int = 10,
    ) -> tuple[list[AudienciaSegmentoItem], int]:
        params = {
            "sexo": sexo,
            "edad_min": edad_min,
            "edad_max": edad_max,
            "ciudad": ciudad,
            "departamento": departamento,
            "concepto": concepto,
            "servicio": servicio,
            "tipo_vinculacion": tipo_vinculacion,
            "ultimo_uso": ultimo_uso,
        }
        return self._ejecutar_pagina(
            _SQL_AUDIENCIA_NO_PLAN_LIGA, params, pagina, por_pagina
        )

    def listar_audiencia_sin_uso(
        self,
        sexo: str | None = None,
        edad_min: int | None = None,
        edad_max: int | None = None,
        ciudad: str | None = None,
        departamento: str | None = None,
        tipo_vinculacion: str | None = None,
        pagina: int = 1,
        por_pagina: int = 10,
    ) -> tuple[list[AudienciaSegmentoItem], int]:
        params = {
            "sexo": sexo,
            "edad_min": edad_min,
            "edad_max": edad_max,
            "ciudad": ciudad,
            "departamento": departamento,
            "tipo_vinculacion": tipo_vinculacion,
        }
        return self._ejecutar_pagina(_SQL_AUDIENCIA_SIN_USO, params, pagina, por_pagina)

    def listar_audiencia_todos(
        self,
        sexo: str | None = None,
        edad_min: int | None = None,
        edad_max: int | None = None,
        ciudad: str | None = None,
        departamento: str | None = None,
        tipo_vinculacion: str | None = None,
        pagina: int = 1,
        por_pagina: int = 10,
    ) -> tuple[list[AudienciaSegmentoItem], int]:
        """Activos de Plan Liga con y sin uso del plan (ver _SQL_AUDIENCIA_TODOS).
        concepto/servicio/ultimo_uso van en None: _SQL_AUDIENCIA los referencia
        como binds, pero en esta audiencia no se filtra por ellos (el servicio
        llama a listar_audiencia cuando vienen, porque solo aplican a quien uso)."""
        params = {
            "sexo": sexo,
            "edad_min": edad_min,
            "edad_max": edad_max,
            "ciudad": ciudad,
            "departamento": departamento,
            "tipo_vinculacion": tipo_vinculacion,
            "concepto": None,
            "servicio": None,
            "ultimo_uso": None,
        }
        return self._ejecutar_pagina(_SQL_AUDIENCIA_TODOS, params, pagina, por_pagina)

    def _valores_distintos(self, sql: str) -> list[str]:
        filas = self.db.execute(text(sql)).scalars().all()
        return [valor for valor in filas if valor]

    def listar_ciudades(self) -> list[str]:
        return self._valores_distintos(_SQL_VALORES_MUNICIPIO)

    def listar_conceptos(self) -> list[str]:
        return self._valores_distintos(_SQL_VALORES_CONCEPTO)

    def listar_servicios(self) -> list[str]:
        return self._valores_distintos(_SQL_VALORES_SERVICIO)

    def _pares_distintos(self, sql: str, clave_a: str, clave_b: str) -> list[dict[str, str]]:
        """Como _valores_distintos pero para 2 columnas relacionadas (ver
        listar_ubicaciones/listar_conceptos_servicios). El driver de Oracle
        puede devolver las claves en minuscula: se normaliza a mayuscula
        antes de acceder por nombre (igual que en _mapear)."""
        filas = self.db.execute(text(sql)).mappings().all()
        resultado = []
        for fila in filas:
            datos = {clave.upper(): valor for clave, valor in fila.items()}
            valor_a = datos.get(clave_a.upper())
            valor_b = datos.get(clave_b.upper())
            if valor_a and valor_b:
                resultado.append({clave_a: valor_a, clave_b: valor_b})
        return resultado

    def listar_ubicaciones(self) -> list[dict[str, str]]:
        """Pares (departamento, municipio) distintos, para el desplegable
        en cascada de Departamento -> Ciudad/municipio."""
        return self._pares_distintos(_SQL_UBICACIONES, "departamento", "municipio")

    def listar_conceptos_servicios(self) -> list[dict[str, str]]:
        """Pares (concepto, servicio) distintos, para el desplegable en
        cascada de Concepto -> Servicio."""
        return self._pares_distintos(_SQL_CONCEPTOS_SERVICIOS, "concepto", "servicio")

    def resumen_uso_plan(self) -> dict[str, int]:
        fila = self.db.execute(text(_SQL_RESUMEN_USO_PLAN)).mappings().first()
        return {clave.upper(): int(valor or 0) for clave, valor in fila.items()}

    def _uso_tmpbi1(self, documento: str) -> tuple[int, str | None]:
        fila = self.db.execute(
            text(_SQL_USO_TMPBI1_POR_DOCUMENTO), {"documento": documento}
        ).mappings().first()
        if fila is None:
            return 0, None
        datos = {clave.upper(): valor for clave, valor in fila.items()}
        return int(datos.get("SERVICIOS_USADOS") or 0), _fecha_iso(datos.get("ULTIMO_USO"))

    def buscar_uso_por_documento(self, documento: str) -> dict | None:
        """Busca el documento como titular; si no aparece, como beneficiario.
        Retorna None si no es ninguno de los dos."""
        fila = self.db.execute(
            text(_SQL_BUSCAR_TITULAR_USO), {"documento": documento}
        ).mappings().first()
        tipo = "titular"
        if fila is None:
            fila = self.db.execute(
                text(_SQL_BUSCAR_BENEFICIARIO_USO), {"documento": documento}
            ).mappings().first()
            tipo = "beneficiario"
        if fila is None:
            return None

        datos = {clave.upper(): valor for clave, valor in fila.items()}
        servicios_usados, ultimo_uso = self._uso_tmpbi1(documento)
        return {
            "documento": datos["DOCUMENTO"],
            "tipo": tipo,
            "nombre": datos["NOMBRE"],
            "estado": "Activo" if datos["ESTADO"] == "A" else "Inactivo",
            "ha_usado": servicios_usados > 0,
            "servicios_usados": servicios_usados,
            "ultimo_uso": ultimo_uso,
        }
