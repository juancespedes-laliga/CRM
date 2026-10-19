import logging
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from fastapi import HTTPException

from app.core.config import settings
from app.modules.integraciones.mailerturbo import client
from app.modules.integraciones.mailerturbo.client import MailerTurboError
from app.modules.integraciones.mailerturbo.schemas import (
    CampanaMT,
    ContactoMT,
    DestinatarioCampanaMT,
    DestinatariosCampanaMT,
    DetalleCampanaMT,
    EnviarCampanaMT,
    EstadisticasCampanaMT,
    FalloContactoMT,
    CorreoContactoMT,
    FiltrosAudienciaMT,
    InfoContactoMT,
    ListaMT,
    ListadoCampanasMT,
    PerfilEnvioMT,
    PlantillaMT,
    ResultadoEnvioCampanaMT,
    ResultadoSincronizacionMT,
    SesionMT,
)
from app.modules.marketing.segmentos.schemas import FiltrosAudiencia
from app.modules.marketing.segmentos.service import SegmentosService

logger = logging.getLogger(__name__)

RE_CORREO = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
# Sincronizar contactos son 2 llamadas por persona (buscar + crear/agregar a lista):
# se hacen en paralelo para no tardar minutos con listas grandes.
HILOS_SINCRONIZACION = 8
# Reportes por campana (ObtenerCorreosEnviadosCampana, ObtenerClicksCampana): MailerTurbo
# acepta paginas de 5000; con el tope se cubren campanas de hasta 250.000 correos.
REGISTROS_REPORTE = 5000
MAX_PAGINAS_REPORTE = 50


def _int(valor: Any, defecto: int = 0) -> int:
    try:
        return int(float(valor))
    except (TypeError, ValueError):
        return defecto


def _float(valor: Any) -> float:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return 0.0


def _texto(valor: Any) -> str | None:
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None


def _error_http(exc: MailerTurboError) -> HTTPException:
    return HTTPException(status_code=502, detail=f"MailerTurbo: {exc.detail}")


class MailerTurboService:
    def __init__(self, segmentos: SegmentosService) -> None:
        self.segmentos = segmentos
        self.idempresa = settings.mailerturbo_idempresa

    def _llamar(self, metodo: str, data: dict[str, Any]) -> Any:
        try:
            return client.llamar(metodo, {"idempresa": self.idempresa, **data})
        except MailerTurboError as exc:
            raise _error_http(exc) from exc

    # ── Catalogos ──────────────────────────────────────────────────────
    @staticmethod
    def _mapear_lista(l: dict[str, Any], titulo_defecto: str = "") -> ListaMT:
        return ListaMT(
            id=_int(l.get("idlista")),
            titulo=l.get("titulolista") or titulo_defecto,
            estado=l.get("estadolista") or "Activa",
            total_correos=_int(l.get("totalcorreoslista")),
            total_activos=_int(l.get("totalactivoslista")),
            total_rebotes=_int(l.get("totalreboteslista")),
            total_salidas=_int(l.get("totalsalidaslista")),
            total_envios=_int(l.get("totalenvioslista")),
            total_vistas=_int(l.get("totalvistaslista")),
            total_clicks=_int(l.get("totalclickslista")),
            total_telefonos=_int(l.get("totaltelefonosactivos")),
            tipo=_texto(l.get("tipolista")),
            fecha_creacion=_texto(l.get("fechacreacionlista")),
        )

    def listar_listas(self) -> list[ListaMT]:
        data = self._llamar("ObtenerListas", {"idlista": [], "q": ""}) or []
        return [self._mapear_lista(l) for l in data]

    def crear_lista(self, titulo: str) -> ListaMT:
        l = self._llamar("CrearLista", {"titulolista": titulo.strip()}) or {}
        return self._mapear_lista(l, titulo.strip())

    # MailerTurbo no tiene un metodo para listar los contactos de una lista: solo
    # se puede consultar un contacto puntual por correo o telefono.
    def buscar_contacto(self, correo: str | None, telefono: str | None) -> InfoContactoMT | None:
        correo = (correo or "").strip().lower()
        telefono = re.sub(r"\D", "", telefono or "")
        if not correo and not telefono:
            raise HTTPException(status_code=400, detail="Indique un correo o un telefono.")
        try:
            c = client.llamar(
                "ObtenerInfoContacto",
                {"idempresa": self.idempresa, "correo": correo, "telefonocontacto": telefono},
            )
        except MailerTurboError as exc:
            if exc.codigo == "WS_RUNMETHOD_ERROR":  # no existe
                return None
            raise _error_http(exc) from exc
        if not isinstance(c, dict):
            return None
        campos = c.get("camposdinamicos") or {}
        return InfoContactoMT(
            id=_int(c.get("idcontacto")),
            nombre=c.get("nombrecontacto") or "",
            apellido=c.get("apellidocontacto") or "",
            telefono=c.get("telefonocontacto") or "",
            correos=[
                CorreoContactoMT(
                    correo=x.get("correo") or "",
                    enviar_campana=x.get("enviarcampana"),
                    estado=x.get("estadocorreo"),
                )
                for x in (c.get("correos") or [])
            ],
            campos_dinamicos={
                str(k): ", ".join(map(str, v)) if isinstance(v, list) else str(v)
                for k, v in (campos.items() if isinstance(campos, dict) else [])
            },
        )

    def listar_plantillas(self) -> list[PlantillaMT]:
        data = self._llamar("ListarPlantillasEmail", {}) or {}
        return [
            PlantillaMT(id=_int(p.get("idplantilla")), nombre=p.get("nombreplantilla") or "")
            for p in data.get("plantillas", [])
        ]

    def listar_perfiles(self) -> list[PerfilEnvioMT]:
        data = self._llamar("ListarPerfilesEnvio", {}) or {}
        return [
            PerfilEnvioMT(
                id=_int(p.get("idperfilenvio")),
                titulo=p.get("tituloperfilenvio") or "",
                correo=p.get("correoperfilenvio") or "",
                estado=p.get("estadoperfilenvio") or "",
            )
            for p in data.get("perfiles", [])
        ]

    def listar_campanas(self, pagina: int, por_pagina: int, q: str | None) -> ListadoCampanasMT:
        filtro: dict[str, Any] = {"registros": por_pagina, "pagina": pagina}
        if q and q.strip():
            filtro["palabraclave"] = q.strip()
        data = self._llamar("ListarCampanas", filtro) or {}
        paginacion = data.get("paginacion") or {}
        campanas = []
        for c in data.get("campanas", []):
            listas = c.get("listas")
            if isinstance(listas, list):
                listas = ", ".join(str(x) for x in listas)
            campanas.append(
                CampanaMT(
                    id=_int(c.get("idcampana")),
                    nombre=c.get("nombrecampana") or "",
                    asunto=_texto(c.get("asuntocampana")),
                    estado=c.get("estadocampana") or "",
                    tipo=c.get("tipocampana") or "",
                    fecha=_texto(c.get("fechacampana")),
                    listas=listas or "",
                    total_envios=_int(c.get("totalenvios")),
                    total_vistas=_int(c.get("totalvistas")),
                    porcentaje_vistas=_float(c.get("porcentajevistas")),
                    total_clicks=_int(c.get("totalclicks")),
                    porcentaje_clicks=_float(c.get("porcentajeclicks")),
                    total_rebotes=_int(c.get("totalrebotes")),
                    total_salidas=_int(c.get("totalsalidas")),
                )
            )
        return ListadoCampanasMT(
            campanas=campanas,
            total=_int(paginacion.get("totalregistros"), len(campanas)),
            total_paginas=max(1, _int(paginacion.get("totalpaginas"), 1)),
        )

    def detalle_campana(self, id_campana: int) -> DetalleCampanaMT:
        data = self._llamar("ObtenerInfoCampana", {"idcampana": id_campana}) or {}
        d = data.get("detalles") or {}
        e = data.get("estadisticas") or {}
        return DetalleCampanaMT(
            id=_int(d.get("idcampana"), id_campana),
            nombre=d.get("nombrecampana") or "",
            asunto=_texto(d.get("asuntocampana")),
            estado=d.get("estadocampana") or "",
            tipo=d.get("tipocampana") or "",
            fecha=_texto(d.get("fechacampana")),
            fecha_programacion=_texto(d.get("fechaprogramacion")),
            perfil_envio=_texto(d.get("tituloperfilenvio")),
            correo_perfil_envio=_texto(d.get("correoperfilenvio")),
            listas=_texto(d.get("nombreslistas")),
            usuario_envio=_texto(d.get("usuarioenvio")),
            estadisticas=EstadisticasCampanaMT(
                total_envios=_int(e.get("totalenvios")),
                total_vistas=_int(e.get("totalvistas")),
                porcentaje_vistas=_float(e.get("porcentajevistas")),
                total_clicks=_int(e.get("totalclicks")),
                porcentaje_clicks=_float(e.get("porcentajeclicks")),
                vistas_landing=_int(e.get("vistaslanding")),
                total_rebotes=_int(e.get("totalrebotes")),
                porcentaje_rebotes=_float(e.get("porcentajerebotes")),
                total_salidas=_int(e.get("totalsalidas")),
                porcentaje_salidas=_float(e.get("porcentajesalidas")),
                total_rechazados=_int(e.get("totalrechazados")),
            ),
        )

    def _todas_las_paginas(self, metodo: str, campo: str, id_campana: int) -> list[dict[str, Any]]:
        """Los reportes de campana vienen paginados: se piden todas las paginas."""
        filas: list[dict[str, Any]] = []
        for pagina in range(1, MAX_PAGINAS_REPORTE + 1):
            data = self._llamar(
                metodo, {"idcampana": id_campana, "registros": REGISTROS_REPORTE, "pagina": pagina}
            ) or {}
            filas.extend(data.get(campo) or [])
            if pagina >= _int((data.get("paginacion") or {}).get("totalpaginas"), 1):
                break
        return filas

    def destinatarios_campana(self, id_campana: int) -> DestinatariosCampanaMT:
        """Todos los correos de la campana con su resultado (enviado, rebote, baja),
        si abrio y si hizo clic. Los links se cruzan desde ObtenerClicksCampana."""
        with ThreadPoolExecutor(max_workers=2) as pool:
            f_envios = pool.submit(
                self._todas_las_paginas, "ObtenerCorreosEnviadosCampana", "correosenviados", id_campana
            )
            f_clicks = pool.submit(self._todas_las_paginas, "ObtenerClicksCampana", "clicks", id_campana)
            envios, clicks = f_envios.result(), f_clicks.result()

        clicks_por_correo: dict[str, list[dict[str, Any]]] = {}
        for c in clicks:
            clicks_por_correo.setdefault((c.get("correo") or "").strip().lower(), []).append(c)

        destinatarios = []
        for f in envios:
            correo = (f.get("correo") or "").strip()
            suyos = clicks_por_correo.get(correo.lower(), [])
            fechas_clic = sorted(x["fechaclick"] for x in suyos if x.get("fechaclick"))
            destinatarios.append(
                DestinatarioCampanaMT(
                    nombre=(f.get("nombreenvio") or "").strip(),
                    correo=correo,
                    telefono=_texto(f.get("telefonoenvio")),
                    estado_envio=f.get("estadoenvio") or "",
                    resultado_envio=f.get("resultadoenvio") or "",
                    fecha_enviado=_texto(f.get("fechaenviado")),
                    abrio=f.get("confirmado") == "Si",
                    fecha_apertura=_texto(f.get("fechaconfirmado")),
                    clic=f.get("clickeado") == "Si" or bool(suyos),
                    fecha_clic=fechas_clic[0] if fechas_clic else None,
                    links=sorted({x["link"] for x in suyos if x.get("link")}),
                    baja=f.get("salida") == "Si",
                    fecha_baja=_texto(f.get("fechasalida")),
                    vista_landing=f.get("vistalanding") == "Si",
                )
            )
        return DestinatariosCampanaMT(destinatarios=destinatarios, total=len(destinatarios))

    # ── Destinatarios ──────────────────────────────────────────────────
    def _contactos_de_audiencia(self, filtros: FiltrosAudienciaMT) -> list[ContactoMT]:
        """Toda la audiencia del filtro (no solo lo cargado en pantalla)."""
        items = self.segmentos.obtener_audiencia_completa(
            FiltrosAudiencia(**filtros.model_dump(exclude={"excluir_documentos"}))
        )
        excluir = {d.strip() for d in filtros.excluir_documentos}
        contactos = []
        for item in items:
            documento = (item.IDENTIFICACION or "").strip()
            if documento and documento in excluir:
                continue
            ciudad = (item.CIUDAD or "").strip()
            contactos.append(
                ContactoMT(
                    nombre=(item.NOMBRES or "").strip(),
                    correo=(item.CORREO or "").strip(),
                    telefono=item.TELEFONO or "",
                    documento=documento or None,
                    ciudad=ciudad or None,
                )
            )
        return contactos

    def _depurar(self, contactos: list[ContactoMT]) -> list[ContactoMT]:
        """Solo correos validos, sin repetir; telefono solo digitos."""
        vistos: set[str] = set()
        limpios = []
        for c in contactos:
            correo = c.correo.strip().lower()
            if not RE_CORREO.match(correo) or correo in vistos:
                continue
            vistos.add(correo)
            limpios.append(
                c.model_copy(
                    update={
                        "correo": correo,
                        "nombre": c.nombre.strip() or correo.split("@")[0],
                        "telefono": re.sub(r"\D", "", c.telefono or ""),
                    }
                )
            )
        return limpios

    def _destinatarios(
        self, contactos: list[ContactoMT], audiencia: FiltrosAudienciaMT | None
    ) -> list[ContactoMT]:
        base = self._contactos_de_audiencia(audiencia) if audiencia else contactos
        return self._depurar(base)

    @staticmethod
    def _contacto_a_mt(c: ContactoMT) -> dict[str, Any]:
        return {
            "nombrecontacto": c.nombre,
            "apellidocontacto": c.apellido,
            "telefonocontacto": c.telefono,
            "correos": [{"correo": c.correo, "enviarcampana": "Si", "estadocorreo": "Activo"}],
        }

    # ── Contactos ──────────────────────────────────────────────────────
    def _sincronizar_uno(
        self, contacto: ContactoMT, id_lista: int, etiquetas: list[str]
    ) -> tuple[str, str | None]:
        """Devuelve ('creado' | 'actualizado' | 'fallido', error)."""
        base = {"idempresa": self.idempresa}
        try:
            existente = None
            try:
                existente = client.llamar("ObtenerInfoContacto", {**base, "correo": contacto.correo})
            except MailerTurboError:
                existente = None  # WS_RUNMETHOD_ERROR = no existe

            if isinstance(existente, dict) and existente.get("idcontacto"):
                # Ya existe: solo se agrega a la lista, sin tocar sus datos ni quitarlo de otras.
                client.llamar(
                    "ActualizarListasContacto",
                    {
                        **base,
                        "idcontacto": _int(existente["idcontacto"]),
                        "idlista": [id_lista],
                        "removerlistas": "No",
                    },
                )
                return "actualizado", None

            datos = {
                **base,
                **self._contacto_a_mt(contacto),
                "idlista": [id_lista],
                "idformularioweb": "",
                "removerlistas": "No",
                "removeretiquetas": "No",
            }
            if etiquetas:
                datos["etiquetas"] = etiquetas
            client.llamar("CrearContacto", datos)
            return "creado", None
        except MailerTurboError as exc:
            return "fallido", exc.detail

    def sincronizar_contactos(
        self,
        id_lista: int,
        contactos: list[ContactoMT],
        audiencia: FiltrosAudienciaMT | None,
        etiquetas: list[str],
    ) -> ResultadoSincronizacionMT:
        if not client.configurado():
            raise _error_http(MailerTurboError("no esta configurado en el servidor."))
        destinatarios = self._destinatarios(contactos, audiencia)
        if not destinatarios:
            raise HTTPException(status_code=400, detail="No hay contactos con correo valido.")

        with ThreadPoolExecutor(max_workers=HILOS_SINCRONIZACION) as pool:
            resultados = list(
                pool.map(lambda c: self._sincronizar_uno(c, id_lista, etiquetas), destinatarios)
            )

        fallos = [
            FalloContactoMT(correo=c.correo, error=err or "Error")
            for c, (estado, err) in zip(destinatarios, resultados)
            if estado == "fallido"
        ]
        return ResultadoSincronizacionMT(
            total=len(destinatarios),
            creados=sum(1 for estado, _ in resultados if estado == "creado"),
            actualizados=sum(1 for estado, _ in resultados if estado == "actualizado"),
            fallidos=len(fallos),
            fallos=fallos,
        )

    # ── Campanas ───────────────────────────────────────────────────────
    def enviar_campana(self, datos: EnviarCampanaMT) -> ResultadoEnvioCampanaMT:
        if bool(datos.id_plantilla) == bool(datos.html and datos.html.strip()):
            raise HTTPException(
                status_code=400, detail="Envie una plantilla de MailerTurbo o el HTML, no ambos."
            )

        data: dict[str, Any] = {
            "nombrecampana": datos.nombre.strip(),
            "asuntocampana": datos.asunto.strip(),
            "idperfilenvio": datos.id_perfil_envio,
        }
        if datos.id_plantilla:
            data["idplantilla"] = datos.id_plantilla
        else:
            data["textocampana"] = datos.html

        total_contactos = None
        if datos.id_listas:
            data["idlista"] = datos.id_listas
        else:
            destinatarios = self._destinatarios(datos.contactos, datos.audiencia)
            if not destinatarios:
                raise HTTPException(status_code=400, detail="No hay destinatarios con correo valido.")
            data["contactos"] = [self._contacto_a_mt(c) for c in destinatarios]
            total_contactos = len(destinatarios)
            if datos.nombre_lista and datos.nombre_lista.strip():
                data["nombrelista"] = datos.nombre_lista.strip()

        if datos.id_listas_excluir:
            data["idlistaExcluir"] = datos.id_listas_excluir
        if datos.fecha_programacion:
            data["fechaprogramacion"] = datos.fecha_programacion

        resultado = self._llamar("EnviarCampanaEmail", data) or {}
        logger.info(
            "MailerTurbo: campana %s creada (%s contactos)", resultado.get("idcampana"), total_contactos
        )
        return ResultadoEnvioCampanaMT(
            id_campana=_int(resultado.get("idcampana")),
            explicacion=None,
            total_contactos=total_contactos,
        )

    # ── Sesion ─────────────────────────────────────────────────────────
    def sesion(self) -> SesionMT:
        try:
            s = client.obtener_token_sesion()
        except MailerTurboError as exc:
            raise _error_http(exc) from exc
        return SesionMT(tokensesion=s["tokensesion"], fecha_expiracion=s.get("fechaexpiracion"))
