from app.core.exceptions import ConflictError, NotFoundError


class TitularNotFoundError(NotFoundError):
    def __init__(self, id_titular: int | str) -> None:
        super().__init__(detail=f"Titular {id_titular} no encontrado")


class TitularAmbiguoError(ConflictError):
    def __init__(self, documento: str) -> None:
        super().__init__(
            detail=(
                f"Existe mas de un titular con el documento {documento}; "
                "no se puede determinar a cual asociar el beneficiario"
            )
        )


class BeneficiarioNotFoundError(NotFoundError):
    def __init__(self, id_beneficiario: int | str) -> None:
        super().__init__(detail=f"Beneficiario {id_beneficiario} no encontrado")


class TitularInactivoError(ConflictError):
    def __init__(self, id_titular: int, accion: str = "activar el beneficiario") -> None:
        super().__init__(
            detail=(
                f"No se pudo {accion} ya que el titular "
                f"{id_titular} esta inactivo"
            )
        )


class BeneficiarioInactivoError(ConflictError):
    def __init__(self, id_beneficiario: int, accion: str = "reemplazar el beneficiario") -> None:
        super().__init__(
            detail=(
                f"No se pudo {accion} ya que el beneficiario "
                f"{id_beneficiario} esta inactivo"
            )
        )


class DocumentoDuplicadoError(ConflictError):
    def __init__(self, documento: str, tipo_registro: str) -> None:
        super().__init__(
            detail=(
                f"El documento {documento} ya esta registrado como "
                f"{tipo_registro.lower()}"
            )
        )


class CupoBeneficiariosExcedidoError(ConflictError):
    def __init__(self, id_titular: int) -> None:
        super().__init__(
            detail=(
                f"El titular {id_titular} ya alcanzo el cupo maximo de "
                f"beneficiarios de su plan"
            )
        )


class CupoPlanInsuficienteError(ConflictError):
    """Se intento cambiar el plan de un titular (ej. al renovar) a uno cuyo
    cupo de beneficiarios es menor a los beneficiarios activos que ya tiene."""

    def __init__(self, id_titular: int, beneficiarios_activos: int, cupo_nuevo_plan: int) -> None:
        super().__init__(
            detail=(
                f"El titular {id_titular} tiene {beneficiarios_activos} beneficiario(s) "
                f"activo(s), pero el plan elegido solo permite {cupo_nuevo_plan}. "
                "Desactiva beneficiarios antes de cambiar a ese plan."
            )
        )
