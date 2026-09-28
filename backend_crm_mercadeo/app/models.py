from datetime import date, datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.enums import EstadoBitacora, EtapaEmbudoNombre, TipoContacto

from .database import Base


class Etiqueta(Base):
    __tablename__ = "mercadeo_crm_etiquetas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str] = mapped_column(String(20))

    contactos: Mapped[list["ContactoEtiqueta"]] = relationship(back_populates="etiqueta")


class ContactoEtiqueta(Base):
    __tablename__ = "mercadeo_crm_contacto_etiqueta"

    contacto_id: Mapped[int] = mapped_column(
        ForeignKey("mercadeo_crm_contactos.id"), primary_key=True
    )
    etiqueta_id: Mapped[int] = mapped_column(
        ForeignKey("mercadeo_crm_etiquetas.id"), primary_key=True
    )
    usuario_id: Mapped[int] = mapped_column(ForeignKey("intranet_usuarios.id"))
    fecha: Mapped[datetime] = mapped_column(DateTime)

    contacto: Mapped["Contacto"] = relationship(back_populates="etiquetas")
    etiqueta: Mapped["Etiqueta"] = relationship(back_populates="contactos")
    usuario: Mapped["Usuario"] = relationship(back_populates="contacto_etiquetas")


class Campana(Base):
    __tablename__ = "mercadeo_crm_campanas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    asunto: Mapped[str] = mapped_column(String(200))
    contenido: Mapped[str] = mapped_column(Text)
    estado: Mapped[str] = mapped_column(String(30))
    fecha_inicio: Mapped[date] = mapped_column(Date)
    fecha_fin: Mapped[date] = mapped_column(Date)
    fecha_creacion: Mapped[datetime | None] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    fecha_actualizacion: Mapped[datetime | None] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    segmentos: Mapped[list["CampanaSegmento"]] = relationship(back_populates="campana")


class Segmento(Base):
    __tablename__ = "mercadeo_crm_segmentos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    filtros: Mapped[str] = mapped_column(Text)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime)
    usuario_id: Mapped[int] = mapped_column(Integer)

    campanas: Mapped[list["CampanaSegmento"]] = relationship(back_populates="segmento")


class CampanaSegmento(Base):
    __tablename__ = "mercadeo_crm_campana_segmento"

    campana_id: Mapped[int] = mapped_column(
        ForeignKey("mercadeo_crm_campanas.id"), primary_key=True
    )
    segmento_id: Mapped[int] = mapped_column(
        ForeignKey("mercadeo_crm_segmentos.id"), primary_key=True
    )
    usuario_id: Mapped[int] = mapped_column(ForeignKey("intranet_usuarios.id"))
    fecha: Mapped[datetime] = mapped_column(DateTime)

    campana: Mapped["Campana"] = relationship(back_populates="segmentos")
    segmento: Mapped["Segmento"] = relationship(back_populates="campanas")
    usuario: Mapped["Usuario"] = relationship(back_populates="campana_segmentos")


class PlantillaCorreo(Base):
    """Plantilla del editor visual de Campanas (ver EditorHtmlGrapes.vue en el
    frontend). `html`/`css` son lo que exporta GrapesJS; `proyecto` es su
    projectData (JSON como texto) para poder reabrirla sin perder estilos."""

    __tablename__ = "mercadeo_crm_plantillas_correo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    asunto: Mapped[str | None] = mapped_column(String(200))
    html: Mapped[str | None] = mapped_column(Text)
    css: Mapped[str | None] = mapped_column(Text)
    proyecto: Mapped[str | None] = mapped_column(Text)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("intranet_usuarios.id"))
    usuario_actualizacion_id: Mapped[int | None] = mapped_column(
        ForeignKey("intranet_usuarios.id")
    )
    fecha_creacion: Mapped[datetime | None] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    fecha_actualizacion: Mapped[datetime | None] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )


# ---------------------------------------------------------------------------
# Modulo: Comercial (CRM Comercial)
#
# FKs internas: definidas aqui con ForeignKey.
# FKs cross-modulo (usuarios): quedan como columnas sin ForeignKey por
# ahora. Se agregan al final.
#
# oportunidades.servicio_id -> intranet_planliga_tipo_plan.id se declara
# con ForeignKey real (la clase PlanLigaTipoPlan vive mas abajo en este
# mismo archivo).
#
# intranet_planliga es una tabla externa (modulo Integraciones) que ya
# existe en la base de datos. Se mapea aqui de forma minima (solo el id)
# para poder declarar FKs reales desde Oportunidad y Bitacora.
# ---------------------------------------------------------------------------


class PlanLiga(Base):
    __tablename__ = "intranet_planliga"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fecha_registro: Mapped[datetime | None] = mapped_column(DateTime)
    estado: Mapped[str | None] = mapped_column(String(2))
    nombre1: Mapped[str | None] = mapped_column(String(20))
    nombre2: Mapped[str | None] = mapped_column(String(20))
    apellido1: Mapped[str | None] = mapped_column(String(20))
    apellido2: Mapped[str | None] = mapped_column(String(20))
    documento: Mapped[str | None] = mapped_column(String(20))
    tipo: Mapped[str | None] = mapped_column(String(2))
    empresa: Mapped[str | None] = mapped_column(String(100))
    correo: Mapped[str | None] = mapped_column(String(200))
    telefono: Mapped[str | None] = mapped_column(String(15))
    fecha_ingreso: Mapped[date | None] = mapped_column(Date)
    fecha_nacimiento: Mapped[date | None] = mapped_column(Date)
    sexo: Mapped[str | None] = mapped_column(String(1))
    direccion: Mapped[str | None] = mapped_column(String(100))
    ciudad: Mapped[str | None] = mapped_column(String(50))
    departamento: Mapped[str | None] = mapped_column(String(50))
    tipo_plan: Mapped[str | None] = mapped_column(String(30))
    tipo_plan_id: Mapped[int | None] = mapped_column(
        ForeignKey("intranet_planliga_tipo_plan.id")
    )
    tipo_afiliado: Mapped[str | None] = mapped_column(String(2))
    eps: Mapped[str | None] = mapped_column(String(100))
    otraeps: Mapped[str | None] = mapped_column(String(100))
    plan_salud: Mapped[str | None] = mapped_column(String(100))
    plan_nombre: Mapped[str | None] = mapped_column(String(100))
    renovado: Mapped[str | None] = mapped_column(String(1))

    oportunidades: Mapped[list["Oportunidad"]] = relationship(back_populates="plan_liga_titular")
    bitacoras: Mapped[list["Bitacora"]] = relationship(back_populates="titular")
    tipo_plan_rel: Mapped["PlanLigaTipoPlan | None"] = relationship(back_populates="titulares")


class PlanLigaBeneficiario(Base):
    __tablename__ = "intranet_planliga_beneficiario"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    planliga_id: Mapped[int | None] = mapped_column(Integer)
    orden: Mapped[int | None] = mapped_column(Integer)
    tipo_plan: Mapped[str | None] = mapped_column(String(30))
    tipo: Mapped[str | None] = mapped_column(String(2))
    documento: Mapped[str | None] = mapped_column(String(20))
    nombre1: Mapped[str | None] = mapped_column(String(20))
    nombre2: Mapped[str | None] = mapped_column(String(20))
    apellido1: Mapped[str | None] = mapped_column(String(20))
    apellido2: Mapped[str | None] = mapped_column(String(20))
    fecha_nacimiento: Mapped[date | None] = mapped_column(Date)
    sexo: Mapped[str | None] = mapped_column(String(1))
    direccion: Mapped[str | None] = mapped_column(String(100))
    ciudad: Mapped[str | None] = mapped_column(String(50))
    departamento: Mapped[str | None] = mapped_column(String(50))
    correo: Mapped[str | None] = mapped_column(String(200))
    telefono: Mapped[str | None] = mapped_column(String(15))
    fecha_ingreso: Mapped[date | None] = mapped_column(Date)
    fecha_registro: Mapped[datetime | None] = mapped_column(DateTime)
    estado: Mapped[str | None] = mapped_column(String(2))
    tipo_afiliado: Mapped[str | None] = mapped_column(String(2))
    empresa: Mapped[str | None] = mapped_column(String(100))
    eps: Mapped[str | None] = mapped_column(String(100))
    otraeps: Mapped[str | None] = mapped_column(String(100))
    plan_salud: Mapped[str | None] = mapped_column(String(100))
    plan_nombre: Mapped[str | None] = mapped_column(String(100))
    actualizado: Mapped[datetime | None] = mapped_column(DateTime)
    factura: Mapped[str | None] = mapped_column(String(20))
    codigo_activacion: Mapped[str | None] = mapped_column(String(20))
    renovado: Mapped[str | None] = mapped_column(String(1))


class TitularColor(Base):
    """Color que el equipo le asigna a mano a un titular (ej. en la pantalla
    de Renovaciones por mes, para marcar visualmente su seguimiento -- "ya
    renovo", "no contesta", etc., igual a como coloreaban filas en Excel).

    Tabla propia del CRM (no se toca intranet_planliga, que es una tabla
    externa/legacy): 1 fila por titular como maximo (unique en titular_id),
    se hace upsert desde el repository en vez de guardar historial."""

    __tablename__ = "mercadeo_crm_titular_color"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    titular_id: Mapped[int] = mapped_column(
        ForeignKey("intranet_planliga.id"), nullable=False, unique=True
    )
    color: Mapped[str] = mapped_column(String(7), nullable=False)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("intranet_usuarios.id"))
    fecha_actualizacion: Mapped[datetime | None] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )


class Empresa(Base):
    __tablename__ = "mercadeo_crm_empresas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    razon_social: Mapped[str] = mapped_column(String(200), nullable=False)
    # Nulo para empresas importadas desde intranet_planliga.empresa (nombre libre sin NIT
    # asociado); sigue siendo unique (Oracle permite varios NULL en una columna unique).
    nit: Mapped[str | None] = mapped_column(String(30), unique=True)
    industria: Mapped[str | None] = mapped_column(String(100))
    direccion: Mapped[str | None] = mapped_column(String(200))
    ciudad: Mapped[str | None] = mapped_column(String(100))
    estado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    responsable_id: Mapped[int | None] = mapped_column(ForeignKey("intranet_usuarios.id"))
    fecha_creacion: Mapped[datetime | None] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    fecha_actualizacion: Mapped[datetime | None] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
    usuario_actualizacion_id: Mapped[int | None] = mapped_column(ForeignKey("intranet_usuarios.id"))

    responsable: Mapped["Usuario | None"] = relationship(
        back_populates="empresas", foreign_keys="Empresa.responsable_id"
    )


class Contacto(Base):
    __tablename__ = "mercadeo_crm_contactos"
    __table_args__ = (
        CheckConstraint(
            "tipo_contacto IS NULL OR tipo_contacto IN ('Cliente', 'Prospecto')",
            name="ck_mercadeo_crm_contactos_tipo_contacto",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tipo_contacto: Mapped[TipoContacto | None] = mapped_column(String(50))
    tipo_documento: Mapped[str | None] = mapped_column(String(20))
    documento: Mapped[str | None] = mapped_column(String(30))
    nombre1: Mapped[str] = mapped_column(String(100), nullable=False)
    nombre2: Mapped[str | None] = mapped_column(String(100))
    apellido1: Mapped[str | None] = mapped_column(String(100))
    apellido2: Mapped[str | None] = mapped_column(String(100))
    sexo: Mapped[str | None] = mapped_column(String(10))
    correo: Mapped[str | None] = mapped_column(String(150))
    telefono: Mapped[str | None] = mapped_column(String(30))
    cargo: Mapped[str | None] = mapped_column(String(100))
    municipio: Mapped[str | None] = mapped_column(String(100))
    departamento: Mapped[str | None] = mapped_column(String(2))
    fecha_nacimiento: Mapped[date | None] = mapped_column(Date)
    estado: Mapped[str | None] = mapped_column(String(30))
    empresa_id: Mapped[int | None] = mapped_column(ForeignKey("mercadeo_crm_empresas.id"))
    responsable_id: Mapped[int | None] = mapped_column(ForeignKey("intranet_usuarios.id"))
    fecha_creacion: Mapped[datetime | None] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    fecha_actualizacion: Mapped[datetime | None] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
    usuario_actualizacion_id: Mapped[int | None] = mapped_column(ForeignKey("intranet_usuarios.id"))

    etiquetas: Mapped[list["ContactoEtiqueta"]] = relationship(
        back_populates="contacto", cascade="all, delete-orphan"
    )
    bitacoras: Mapped[list["Bitacora"]] = relationship(cascade="all, delete-orphan")
    oportunidades: Mapped[list["Oportunidad"]] = relationship(cascade="all, delete-orphan")
    responsable: Mapped["Usuario | None"] = relationship(
        back_populates="contactos", foreign_keys="Contacto.responsable_id"
    )
    empresa: Mapped["Empresa | None"] = relationship()


class Embudo(Base):
    __tablename__ = "mercadeo_crm_embudos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(255))


class EtapaEmbudo(Base):
    __tablename__ = "mercadeo_crm_etapas_embudo"
    __table_args__ = (
        CheckConstraint(
            "nombre IN ('Lead', 'Primer Contacto', 'Reunión', 'Cotización', "
            "'Negociación', 'Ganada', 'Perdida')",
            name="ck_mercadeo_crm_etapas_embudo_nombre",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    embudo_id: Mapped[int | None] = mapped_column(ForeignKey("mercadeo_crm_embudos.id"))
    nombre: Mapped[EtapaEmbudoNombre] = mapped_column(String(100), nullable=False)
    orden: Mapped[int | None] = mapped_column(Integer)


class Oportunidad(Base):
    __tablename__ = "mercadeo_crm_oportunidades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    empresa_id: Mapped[int | None] = mapped_column(ForeignKey("mercadeo_crm_empresas.id"))
    contacto_id: Mapped[int | None] = mapped_column(ForeignKey("mercadeo_crm_contactos.id"))
    servicio_id: Mapped[int | None] = mapped_column(
        ForeignKey("intranet_planliga_tipo_plan.id")
    )
    # Texto libre: servicio_id (FK a intranet_planliga_tipo_plan, ver relationship "servicio"
    # abajo) es especifico del catalogo de planes Plan Liga y no cubre las categorias que
    # ofrece el CRM Comercial (Tamizajes, Brigadas de Salud, etc.), asi que el servicio
    # elegido en el formulario viaja en esta columna en paralelo.
    servicio_nombre: Mapped[str | None] = mapped_column(String(150))
    etapa_id: Mapped[int | None] = mapped_column(ForeignKey("mercadeo_crm_etapas_embudo.id"))
    responsable_id: Mapped[int | None] = mapped_column(ForeignKey("intranet_usuarios.id"))
    valor: Mapped[float | None] = mapped_column(Float)
    probabilidad: Mapped[float | None] = mapped_column(Float)
    estado: Mapped[str | None] = mapped_column(String(30))
    plan_liga_titular_id: Mapped[int | None] = mapped_column(ForeignKey("intranet_planliga.id"))
    fecha_creacion: Mapped[datetime | None] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    fecha_actualizacion: Mapped[datetime | None] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
    usuario_actualizacion_id: Mapped[int | None] = mapped_column(ForeignKey("intranet_usuarios.id"))

    servicio: Mapped["PlanLigaTipoPlan | None"] = relationship(back_populates="oportunidades")
    plan_liga_titular: Mapped["PlanLiga | None"] = relationship(back_populates="oportunidades")
    responsable: Mapped["Usuario | None"] = relationship(
        back_populates="oportunidades", foreign_keys="Oportunidad.responsable_id"
    )
    bitacoras: Mapped[list["Bitacora"]] = relationship(cascade="all, delete-orphan")


class Bitacora(Base):
    __tablename__ = "mercadeo_crm_bitacora"
    __table_args__ = (
        CheckConstraint(
            "estado IN ('pendiente', 'realizado')", name="ck_mercadeo_crm_bitacora_estado"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("intranet_usuarios.id"))
    contacto_id: Mapped[int | None] = mapped_column(ForeignKey("mercadeo_crm_contactos.id"))
    nombre_empresa: Mapped[str | None] = mapped_column(String(200))
    oportunidad_id: Mapped[int | None] = mapped_column(ForeignKey("mercadeo_crm_oportunidades.id"))
    titular_id: Mapped[int | None] = mapped_column(ForeignKey("intranet_planliga.id"))
    tipo: Mapped[str | None] = mapped_column(String(50))
    descripcion: Mapped[str | None] = mapped_column(Text)
    proximo_paso: Mapped[str | None] = mapped_column(Text)
    fecha: Mapped[datetime | None] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    estado: Mapped[EstadoBitacora] = mapped_column(
        String(20), nullable=False, default=EstadoBitacora.PENDIENTE
    )
    fecha_actualizacion: Mapped[datetime | None] = mapped_column(
        DateTime, onupdate=lambda: datetime.now(timezone.utc)
    )
    usuario_actualizacion_id: Mapped[int | None] = mapped_column(ForeignKey("intranet_usuarios.id"))

    titular: Mapped["PlanLiga | None"] = relationship(back_populates="bitacoras")
    usuario: Mapped["Usuario | None"] = relationship(
        back_populates="bitacoras", foreign_keys="Bitacora.usuario_id"
    )


# ---------------------------------------------------------------------------
# Modulo: Servicios y Proveedores
#
# FKs internas (definidas aqui con ForeignKey):
#   - actividad.proveedor_id -> proveedores.id     [1 proveedor : 0..* actividades]
#
# FKs cross ENTRANTES (declaradas en el modulo Comercial/Integraciones,
# informativas):
#   - mercadeo_crm_oportunidades.servicio_id -> intranet_planliga_tipo_plan.id
#   - intranet_planliga.tipo_plan_id -> intranet_planliga_tipo_plan.id
#
# intranet_usuarios e intranet_planliga_tipo_plan son tablas externas que
# ya existen en la base de datos (la segunda reemplaza a las antiguas
# mercadeo_crm_servicios / mercadeo_crm_titular_servicios, eliminadas: un
# titular ahora tiene un unico tipo de plan via PlanLiga.tipo_plan_id, sin
# tabla intermedia).
# ---------------------------------------------------------------------------


class Usuario(Base):
    __tablename__ = "intranet_usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario: Mapped[str | None] = mapped_column(String(50))
    nombres: Mapped[str | None] = mapped_column(String(50))
    contrasena: Mapped[str | None] = mapped_column(String(100))
    estado: Mapped[str | None] = mapped_column(String(20))
    portal_rol: Mapped[str | None] = mapped_column("PORTAL_ROL", String(50))
    id_clase: Mapped[int | None] = mapped_column(Integer)
    id_area: Mapped[int | None] = mapped_column(Integer)
    num_id: Mapped[int | None] = mapped_column(Integer)

    importaciones: Mapped[list["Importacion"]] = relationship(back_populates="usuario")
    contacto_etiquetas: Mapped[list["ContactoEtiqueta"]] = relationship(back_populates="usuario")
    campana_segmentos: Mapped[list["CampanaSegmento"]] = relationship(back_populates="usuario")
    empresas: Mapped[list["Empresa"]] = relationship(
        back_populates="responsable", foreign_keys="Empresa.responsable_id"
    )
    contactos: Mapped[list["Contacto"]] = relationship(
        back_populates="responsable", foreign_keys="Contacto.responsable_id"
    )
    oportunidades: Mapped[list["Oportunidad"]] = relationship(
        back_populates="responsable", foreign_keys="Oportunidad.responsable_id"
    )
    bitacoras: Mapped[list["Bitacora"]] = relationship(
        back_populates="usuario", foreign_keys="Bitacora.usuario_id"
    )


class Proveedor(Base):
    __tablename__ = "mercadeo_crm_proveedores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    categoria: Mapped[str | None] = mapped_column(String(100))
    nit: Mapped[str | None] = mapped_column(String(30))
    correo: Mapped[str | None] = mapped_column(String(150))
    telefono: Mapped[str | None] = mapped_column(String(30))
    estado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    fecha_creacion: Mapped[datetime | None] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    fecha_actualizacion: Mapped[datetime | None] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
    usuario_actualizacion_id: Mapped[int | None] = mapped_column(ForeignKey("intranet_usuarios.id"))
    usuario_creacion_id: Mapped[int | None] = mapped_column(ForeignKey("intranet_usuarios.id"))

    actividades: Mapped[list["Actividad"]] = relationship(cascade="all, delete-orphan")


class Actividad(Base):
    __tablename__ = "mercadeo_crm_actividad"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    cantidad: Mapped[float | None] = mapped_column(Float)
    precio: Mapped[float | None] = mapped_column(Float)
    descripcion: Mapped[str | None] = mapped_column(String(255))
    proveedor_id: Mapped[int | None] = mapped_column(ForeignKey("mercadeo_crm_proveedores.id"))
    fecha_creacion: Mapped[datetime | None] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    fecha_actualizacion: Mapped[datetime | None] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
    usuario_actualizacion_id: Mapped[int | None] = mapped_column(ForeignKey("intranet_usuarios.id"))


class PlanLigaTipoPlan(Base):
    __tablename__ = "intranet_planliga_tipo_plan"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    beneficiarios: Mapped[int] = mapped_column(Integer, nullable=False)
    fecha_registro: Mapped[datetime | None] = mapped_column(DateTime)
    estado: Mapped[str | None] = mapped_column(String(2))
    categoria: Mapped[str | None] = mapped_column(String(50))
    tipo_cliente: Mapped[str | None] = mapped_column(String(30))
    beneficiarios_adicionales: Mapped[int | None] = mapped_column(Integer)
    descripcion: Mapped[str | None] = mapped_column(String(500))

    titulares: Mapped[list["PlanLiga"]] = relationship(back_populates="tipo_plan_rel")
    oportunidades: Mapped[list["Oportunidad"]] = relationship(back_populates="servicio")


class Importacion(Base):
    """Historial de procesos por lote del CRM: cada fila es una corrida (una
    importacion por Excel, un envio masivo de correos, etc.), distinguidas
    por `tipo`. Nacio solo para importaciones (de ahi el nombre de la clase y
    columnas como `archivo`), pero la tabla fisica se renombro a un nombre
    generico (`mercadeo_crm_historial_procesos`) para reutilizarla en otros
    procesos por lote sin crear una tabla nueva por cada uno - ver
    modules/notificaciones/correos (tipo 'correo_vencimiento_plan_liga')."""

    __tablename__ = "mercadeo_crm_historial_procesos"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("intranet_usuarios.id"))
    tipo: Mapped[str | None] = mapped_column(String(50))
    archivo: Mapped[str | None] = mapped_column(String(255))
    registros: Mapped[int | None] = mapped_column(Integer)
    errores: Mapped[int | None] = mapped_column(Integer)
    # Detalle fila por fila (mensajes de error/avisos), guardado como JSON en texto; None en
    # importaciones creadas antes de esta columna.
    detalle_errores: Mapped[str | None] = mapped_column(Text)
    avisos: Mapped[str | None] = mapped_column(Text)
    fecha: Mapped[datetime | None] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    usuario: Mapped["Usuario | None"] = relationship(back_populates="importaciones")


# ---------------------------------------------------------------------------
# Modulo: Permisos (esquema compartido del Intranet, ver readme/DIAGRAMA_BASE_DATOS.md)
#
# Estas 4 tablas ya existen en Oracle (las administra el Intranet/SSO, no
# este backend) y son compartidas entre apps via la columna SISTEMA - aqui
# solo se mapean para poder leerlas. El punto de entrada para consultarlas
# es AuthRepository.obtener_permisos() en app/modules/auth/repository.py.
# ---------------------------------------------------------------------------


class RolApp(Base):
    __tablename__ = "intranet_roles_app"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    sistema: Mapped[str] = mapped_column(String(50))
    fecha_creado: Mapped[datetime | None] = mapped_column(DateTime)
    fecha_actualizado: Mapped[datetime | None] = mapped_column(DateTime)


class PermisoApp(Base):
    __tablename__ = "intranet_permisos_app"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sistema: Mapped[str] = mapped_column(String(50))
    modulo: Mapped[str] = mapped_column(String(100))
    accion: Mapped[str] = mapped_column(String(50))
    fecha_creado: Mapped[datetime | None] = mapped_column(DateTime)
    fecha_actualizado: Mapped[datetime | None] = mapped_column(DateTime)


class RolPermisoApp(Base):
    __tablename__ = "intranet_roles_permisos_app"

    permiso_id: Mapped[int] = mapped_column(
        ForeignKey("intranet_permisos_app.id"), primary_key=True
    )
    rol_id: Mapped[int] = mapped_column(ForeignKey("intranet_roles_app.id"), primary_key=True)


class UsuarioRolApp(Base):
    __tablename__ = "intranet_usuario_rol_app"

    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("intranet_usuarios.id"), primary_key=True
    )
    rol_id: Mapped[int] = mapped_column(ForeignKey("intranet_roles_app.id"), primary_key=True)
    sistema: Mapped[str] = mapped_column(String(50), primary_key=True)
    fecha_creado: Mapped[datetime | None] = mapped_column(DateTime)
    fecha_actualizado: Mapped[datetime | None] = mapped_column(DateTime)
