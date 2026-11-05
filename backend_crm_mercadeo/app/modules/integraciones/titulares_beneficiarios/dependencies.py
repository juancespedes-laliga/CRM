from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.modules.administracion.auditoria.contexto import ContextoAuditoria, contexto_auditoria
from app.modules.integraciones.titulares_beneficiarios.service import (
    TitularesBeneficiariosService,
)


def get_titulares_beneficiarios_service(
    db: Session = Depends(get_db),
    contexto: ContextoAuditoria = Depends(contexto_auditoria),
) -> TitularesBeneficiariosService:
    # El contexto (usuario, IP, origen) queda en el service para auditar cada accion.
    return TitularesBeneficiariosService(db, contexto)
