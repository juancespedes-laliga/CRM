from fastapi import Depends

from app.modules.integraciones.mailerturbo.service import MailerTurboService
from app.modules.marketing.segmentos.dependencies import get_segmentos_service
from app.modules.marketing.segmentos.service import SegmentosService


def get_mailerturbo_service(
    segmentos: SegmentosService = Depends(get_segmentos_service),
) -> MailerTurboService:
    return MailerTurboService(segmentos)
