from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import get_current_username
from app.modules.integraciones.mailerturbo.dependencies import get_mailerturbo_service
from app.modules.integraciones.mailerturbo.schemas import (
    CrearListaMT,
    DestinatariosCampanaMT,
    DetalleCampanaMT,
    EnviarCampanaMT,
    InfoContactoMT,
    ListadoCampanasMT,
    ListadoListasMT,
    ListadoPerfilesMT,
    ListadoPlantillasMT,
    ListaMT,
    ResultadoEnvioCampanaMT,
    ResultadoSincronizacionMT,
    SesionMT,
    SincronizarContactosMT,
)
from app.modules.integraciones.mailerturbo.service import MailerTurboService

# Proxy hacia el Web Service de MailerTurbo: las credenciales (ws_login, idempresa)
# viven solo aqui, el frontend nunca las ve. Ver client.py.
router = APIRouter(
    prefix="/mailerturbo",
    tags=["MailerTurbo"],
    dependencies=[Depends(get_current_username)],
)


@router.get("/listas", response_model=ListadoListasMT)
def listar_listas(service: MailerTurboService = Depends(get_mailerturbo_service)) -> ListadoListasMT:
    return ListadoListasMT(listas=service.listar_listas())


@router.post("/listas", response_model=ListaMT, status_code=status.HTTP_201_CREATED)
def crear_lista(
    datos: CrearListaMT, service: MailerTurboService = Depends(get_mailerturbo_service)
) -> ListaMT:
    return service.crear_lista(datos.titulo)


@router.get("/plantillas", response_model=ListadoPlantillasMT)
def listar_plantillas(
    service: MailerTurboService = Depends(get_mailerturbo_service),
) -> ListadoPlantillasMT:
    return ListadoPlantillasMT(plantillas=service.listar_plantillas())


@router.get("/perfiles-envio", response_model=ListadoPerfilesMT)
def listar_perfiles(
    service: MailerTurboService = Depends(get_mailerturbo_service),
) -> ListadoPerfilesMT:
    return ListadoPerfilesMT(perfiles=service.listar_perfiles())


@router.get("/campanas", response_model=ListadoCampanasMT)
def listar_campanas(
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(20, ge=1, le=200),
    q: str | None = Query(None, description="Filtra por nombre o asunto."),
    service: MailerTurboService = Depends(get_mailerturbo_service),
) -> ListadoCampanasMT:
    return service.listar_campanas(pagina, por_pagina, q)


@router.get("/campanas/{id_campana}", response_model=DetalleCampanaMT)
def detalle_campana(
    id_campana: int, service: MailerTurboService = Depends(get_mailerturbo_service)
) -> DetalleCampanaMT:
    return service.detalle_campana(id_campana)


# Todos los correos de la campana con su resultado; el frontend pagina, filtra y exporta.
@router.get("/campanas/{id_campana}/destinatarios", response_model=DestinatariosCampanaMT)
def destinatarios_campana(
    id_campana: int, service: MailerTurboService = Depends(get_mailerturbo_service)
) -> DestinatariosCampanaMT:
    return service.destinatarios_campana(id_campana)


# Busca UN contacto en MailerTurbo por correo o telefono (la API no permite
# listar los contactos de una lista). null = no existe.
@router.get("/contactos/buscar", response_model=InfoContactoMT | None)
def buscar_contacto(
    correo: str | None = Query(None),
    telefono: str | None = Query(None),
    service: MailerTurboService = Depends(get_mailerturbo_service),
) -> InfoContactoMT | None:
    return service.buscar_contacto(correo, telefono)


# Crea o agrega a la lista cada contacto (por correo). Acepta contactos sueltos
# (Excel/CSV, seleccion de Audiencias) o `audiencia` = filtros de Audiencias para
# tomar a TODAS las personas del filtro.
@router.post("/contactos/sincronizar", response_model=ResultadoSincronizacionMT)
def sincronizar_contactos(
    datos: SincronizarContactosMT,
    service: MailerTurboService = Depends(get_mailerturbo_service),
) -> ResultadoSincronizacionMT:
    return service.sincronizar_contactos(
        datos.id_lista, datos.contactos, datos.audiencia, datos.etiquetas
    )


# Crea la campana en MailerTurbo (EnviarCampanaEmail): queda "En espera" y
# MailerTurbo la envia (o la programa si trae fecha_programacion).
@router.post("/campanas/enviar", response_model=ResultadoEnvioCampanaMT)
def enviar_campana(
    datos: EnviarCampanaMT,
    username: str = Depends(get_current_username),
    service: MailerTurboService = Depends(get_mailerturbo_service),
) -> ResultadoEnvioCampanaMT:
    return service.enviar_campana(datos)


# Token del afiliado para abrir MailerTurbo ya logueado. Se reutiliza el guardado
# hasta que vence; si vencio, se inicia sesion de nuevo (ver client.obtener_token_sesion).
@router.post("/sesion", response_model=SesionMT)
def obtener_sesion(service: MailerTurboService = Depends(get_mailerturbo_service)) -> SesionMT:
    return service.sesion()
