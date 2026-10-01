"""
Sincroniza los PERMISOS del sistema CRM_MERCADEO desde PRODUCCION hacia PRUEBAS.

Copia, SOLO lo que falte (idempotente, se puede correr varias veces sin duplicar):
  - intranet_roles_app          (roles de CRM_MERCADEO)
  - intranet_permisos_app       (permisos = modulo + accion)
  - intranet_roles_permisos_app (que permiso tiene cada rol)

NO toca intranet_usuario_rol_app (asignacion a usuarios) ni ninguna otra tabla.

Los IDs NO se copian: esas tablas son compartidas con otros sistemas del
Intranet, asi que un mismo id puede estar usado por otro sistema en pruebas.
Por eso aqui se empareja por CLAVE NATURAL:
    rol     -> (sistema, nombre)
    permiso -> (sistema, modulo, accion)
y los IDs nuevos se calculan como MAX(id) global de la tabla destino + N.

-------------------------------------------------------------------------------
COMO USARLO
-------------------------------------------------------------------------------
Ambas conexiones salen de backend_crm_mercadeo/.env:

1. DESTINO (pruebas): bloque SCSE_DB_* (el que ya usa el backend, usuario "onco").
   No hay que configurar nada extra.

2. ORIGEN (produccion): bloque PROD_DB_* (usuario "BDLIGA"). Ejemplo:
       PROD_DB_USER=BDLIGA
       PROD_DB_PASSWD=...
       PROD_DB_IP=160.1.1.99
       PROD_DB_PORT=1521
       PROD_DB_DATABASE=scse
   (El backend ignora estas claves extra; solo las usa este script.)

3. Correr con el Python del venv del backend:
       # primero en seco (NO escribe nada, solo muestra que insertaria):
       backend_crm_mercadeo\venv\Scripts\python.exe prueba.py
       # cuando estes conforme, aplicar de verdad:
       backend_crm_mercadeo\venv\Scripts\python.exe prueba.py --apply
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

SISTEMA = "CRM_MERCADEO"

BASE_DIR = Path(__file__).resolve().parent
ENV_DESTINO = BASE_DIR / "backend_crm_mercadeo" / ".env"


def _oracle_url(user: str, passwd: str, ip: str, port: str, database: str) -> str:
    return (
        f"oracle+oracledb://{user}:{passwd}"
        f"@{ip}:{port}/?service_name={database}"
    )


def _fail(msg: str) -> "None":
    print(f"ERROR: {msg}")
    sys.exit(1)


def engine_destino() -> Engine:
    """Pruebas: reutiliza SCSE_DB_* del .env del backend (o del entorno)."""
    cfg = {**dotenv_values(ENV_DESTINO), **os.environ} if ENV_DESTINO.exists() else dict(os.environ)
    faltan = [k for k in ("SCSE_DB_USER", "SCSE_DB_PASSWD", "SCSE_DB_IP", "SCSE_DB_DATABASE") if not cfg.get(k)]
    if faltan:
        _fail(f"Faltan datos del DESTINO (pruebas): {', '.join(faltan)} en {ENV_DESTINO}")
    return create_engine(_oracle_url(
        cfg["SCSE_DB_USER"], cfg["SCSE_DB_PASSWD"], cfg["SCSE_DB_IP"],
        cfg.get("SCSE_DB_PORT", "1521"), cfg["SCSE_DB_DATABASE"],
    ))


def engine_origen() -> Engine:
    """Produccion: bloque PROD_DB_* del .env del backend (o del entorno)."""
    cfg = {**dotenv_values(ENV_DESTINO), **os.environ} if ENV_DESTINO.exists() else dict(os.environ)
    faltan = [k for k in ("PROD_DB_USER", "PROD_DB_PASSWD", "PROD_DB_IP", "PROD_DB_DATABASE") if not cfg.get(k)]
    if faltan:
        _fail(
            "Faltan datos del ORIGEN (produccion): " + ", ".join(faltan) +
            f".\n  Agrega el bloque PROD_DB_* en {ENV_DESTINO} (ver instrucciones al inicio de este archivo)."
        )
    return create_engine(_oracle_url(
        cfg["PROD_DB_USER"], cfg["PROD_DB_PASSWD"], cfg["PROD_DB_IP"],
        cfg.get("PROD_DB_PORT", "1521"), cfg["PROD_DB_DATABASE"],
    ))


def sincronizar(apply: bool) -> None:
    src = engine_origen()
    dst = engine_destino()

    # --- 1) Leer de PRODUCCION (clave natural) ---------------------------------
    with src.connect() as c:
        roles_src = c.execute(text(
            "SELECT nombre FROM intranet_roles_app WHERE sistema = :s"
        ), {"s": SISTEMA}).scalars().all()

        permisos_src = c.execute(text(
            "SELECT modulo, accion FROM intranet_permisos_app WHERE sistema = :s"
        ), {"s": SISTEMA}).all()

        # mapeo rol<->permiso resuelto a claves naturales (rol_nombre, modulo, accion)
        mapeo_src = c.execute(text(
            """
            SELECT r.nombre, p.modulo, p.accion
            FROM intranet_roles_permisos_app rp
            JOIN intranet_roles_app    r ON r.id = rp.rol_id     AND r.sistema = :s
            JOIN intranet_permisos_app p ON p.id = rp.permiso_id AND p.sistema = :s
            """
        ), {"s": SISTEMA}).all()

    print(f"PRODUCCION ({SISTEMA}): {len(roles_src)} roles, "
          f"{len(permisos_src)} permisos, {len(mapeo_src)} asignaciones rol-permiso.")

    with dst.begin() as c:
        # --- 2) Roles faltantes ------------------------------------------------
        roles_dst = {n for (n,) in c.execute(text(
            "SELECT nombre FROM intranet_roles_app WHERE sistema = :s"
        ), {"s": SISTEMA})}
        roles_nuevos = [n for n in roles_src if n not in roles_dst]

        next_id = (c.execute(text("SELECT NVL(MAX(id),0) FROM intranet_roles_app")).scalar() or 0)
        for nombre in roles_nuevos:
            next_id += 1
            if apply:
                c.execute(text(
                    "INSERT INTO intranet_roles_app (id, nombre, sistema, fecha_creado, fecha_actualizado) "
                    "VALUES (:id, :nombre, :s, SYSDATE, SYSDATE)"
                ), {"id": next_id, "nombre": nombre, "s": SISTEMA})
            print(f"  [rol]     {'+ insertar' if apply else '~ (dry-run)'}: {nombre}")

        # --- 3) Permisos faltantes --------------------------------------------
        permisos_dst = {(m, a) for (m, a) in c.execute(text(
            "SELECT modulo, accion FROM intranet_permisos_app WHERE sistema = :s"
        ), {"s": SISTEMA})}
        permisos_nuevos = [(m, a) for (m, a) in permisos_src if (m, a) not in permisos_dst]

        next_id = (c.execute(text("SELECT NVL(MAX(id),0) FROM intranet_permisos_app")).scalar() or 0)
        for modulo, accion in permisos_nuevos:
            next_id += 1
            if apply:
                c.execute(text(
                    "INSERT INTO intranet_permisos_app (id, sistema, modulo, accion, fecha_creado, fecha_actualizado) "
                    "VALUES (:id, :s, :m, :a, SYSDATE, SYSDATE)"
                ), {"id": next_id, "s": SISTEMA, "m": modulo, "a": accion})
            print(f"  [permiso] {'+ insertar' if apply else '~ (dry-run)'}: {modulo}.{accion}")

        # --- 4) Mapeo rol<->permiso faltante (resolviendo IDs ya en destino) ---
        rol_id = {n: i for (i, n) in c.execute(text(
            "SELECT id, nombre FROM intranet_roles_app WHERE sistema = :s"
        ), {"s": SISTEMA})}
        permiso_id = {(m, a): i for (i, m, a) in c.execute(text(
            "SELECT id, modulo, accion FROM intranet_permisos_app WHERE sistema = :s"
        ), {"s": SISTEMA})}
        mapeo_dst = {(r, p) for (r, p) in c.execute(text(
            "SELECT rol_id, permiso_id FROM intranet_roles_permisos_app"
        ))}

        nuevos_mapeos = 0
        omitidos = 0
        for r_nombre, modulo, accion in mapeo_src:
            rid = rol_id.get(r_nombre)
            pid = permiso_id.get((modulo, accion))
            if rid is None or pid is None:
                # En dry-run el rol/permiso aun no existe en destino -> no se puede resolver todavia.
                omitidos += 1
                continue
            if (rid, pid) in mapeo_dst:
                continue
            if apply:
                c.execute(text(
                    "INSERT INTO intranet_roles_permisos_app (rol_id, permiso_id) VALUES (:r, :p)"
                ), {"r": rid, "p": pid})
                mapeo_dst.add((rid, pid))
            nuevos_mapeos += 1
            print(f"  [mapeo]   {'+ insertar' if apply else '~ (dry-run)'}: {r_nombre} -> {modulo}.{accion}")

    print("-" * 70)
    print(f"Roles nuevos:    {len(roles_nuevos)}")
    print(f"Permisos nuevos: {len(permisos_nuevos)}")
    print(f"Mapeos nuevos:   {nuevos_mapeos}")
    if omitidos and not apply:
        print(f"Mapeos no evaluados en seco: {omitidos} "
              f"(dependen de roles/permisos que aun no existen; apareceran al correr con --apply).")
    if apply:
        print("APLICADO. Cambios confirmados en PRUEBAS.")
    else:
        print("DRY-RUN. No se escribio nada. Vuelve a correr con  --apply  para aplicar.")


if __name__ == "__main__":
    sincronizar(apply="--apply" in sys.argv)
