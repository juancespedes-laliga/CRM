from fastapi import FastAPI

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.core.middleware import setup_middlewares
from app.modules.administracion.bitacora.router import router as bitacora_router
from app.modules.administracion.importaciones.router import router as importaciones_router
from app.modules.administracion.usuarios_roles.router import router as usuarios_roles_router
from app.modules.auth.router import router as auth_router
from app.modules.comercial.contactos.router import router as contactos_router
from app.modules.comercial.empresas.router import router as empresas_router
from app.modules.comercial.oportunidades.router import router as oportunidades_router
from app.modules.comercial.tablero.router import router as tablero_router
from app.modules.compartidos.ubicaciones.router import router as ubicaciones_router
from app.modules.integraciones.mailerturbo.router import router as mailerturbo_router
from app.modules.marketing.etiquetas.router import router as etiquetas_router
from app.modules.marketing.plantillas.router import router as plantillas_router
from app.modules.marketing.segmentos.router import router as segmentos_router
from app.modules.notificaciones.correos.router import router as correos_router
from app.modules.servicios_proveedores.actividades.router import router as actividades_router
from app.modules.servicios_proveedores.proveedores.router import router as proveedores_router
from app.modules.servicios_proveedores.servicios.router import router as servicios_router
from app.modules.integraciones.titulares_beneficiarios.router import (
    router as titulares_beneficiarios_router,
)

setup_logging()

app = FastAPI(title=settings.app_name)

setup_middlewares(app)
register_exception_handlers(app)

app.include_router(actividades_router, prefix=settings.api_prefix)
app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(bitacora_router, prefix=settings.api_prefix)
app.include_router(contactos_router, prefix=settings.api_prefix)
app.include_router(correos_router, prefix=settings.api_prefix)
app.include_router(empresas_router, prefix=settings.api_prefix)
app.include_router(etiquetas_router, prefix=settings.api_prefix)
app.include_router(importaciones_router, prefix=settings.api_prefix)
app.include_router(mailerturbo_router, prefix=settings.api_prefix)
app.include_router(oportunidades_router, prefix=settings.api_prefix)
app.include_router(plantillas_router, prefix=settings.api_prefix)
app.include_router(proveedores_router, prefix=settings.api_prefix)
app.include_router(segmentos_router, prefix=settings.api_prefix)
app.include_router(servicios_router, prefix=settings.api_prefix)
app.include_router(tablero_router, prefix=settings.api_prefix)
app.include_router(ubicaciones_router, prefix=settings.api_prefix)
app.include_router(titulares_beneficiarios_router, prefix=settings.api_prefix)
app.include_router(usuarios_roles_router, prefix=settings.api_prefix)


@app.get("/health")
async def health():
    return {"status": "ok"}
