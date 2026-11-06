"""/mobile/v1/incidents/{key}"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from incidentdesk.api.mobile_incident_list import MobileIncidentItem
from incidentdesk.db import get_session
from incidentdesk.models import Incident
from incidentdesk.schemas import TimelineEventOut

router = APIRouter(prefix="/mobile/v1/incidents", tags=["mobile"])


class MobileIncidentDetail(MobileIncidentItem):
    timeline: list[TimelineEventOut]


class MobileNotFound(BaseModel):
    error: str


@router.get("/{key}", response_model=MobileIncidentDetail, responses={404: {"model": MobileNotFound}})
def mobile_incident_detail(key: str, session: Session = Depends(get_session)):
    incident = session.scalar(select(Incident).where(Incident.key == key))
    if not incident:
        return JSONResponse(status_code=404, content={"error": "not_found"})
    return MobileIncidentDetail(
        key=incident.key, title=incident.title, service=incident.service.slug, priority=incident.priority,
        status=incident.status, opened_at=incident.opened_at,
        timeline=[TimelineEventOut.model_validate(e) for e in sorted(incident.events, key=lambda e: e.at)],
    )
