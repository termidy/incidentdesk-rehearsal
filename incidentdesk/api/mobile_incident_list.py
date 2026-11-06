"""The mobile incident list."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from incidentdesk.db import get_session
from incidentdesk.models import Incident, Service

router = APIRouter(prefix="/mobile/v1/incidents", tags=["mobile incidents"])
PAGE_SIZE = 20


class MobileIncidentItem(BaseModel):
    key: str
    title: str
    service: str
    priority: str
    status: str
    opened_at: datetime


class MobileIncidentList(BaseModel):
    items: list[MobileIncidentItem]
    next_page: int | None


@router.get("", response_model=MobileIncidentList)
def list_mobile_incidents(page: int = Query(1, ge=1), session: Session = Depends(get_session)):
    incidents = list(
        session.scalars(
            select(Incident)
            .join(Service)
            .where(Incident.status != "resolved")
            .order_by(Incident.opened_at.desc(), Incident.id.desc())
            .limit(PAGE_SIZE + 1)
            .offset((page - 1) * PAGE_SIZE)
        )
    )
    has_next_page = len(incidents) > PAGE_SIZE
    return MobileIncidentList(
        items=[
            MobileIncidentItem(
                key=incident.key,
                title=incident.title,
                service=incident.service.slug,
                priority=incident.priority,
                status=incident.status,
                opened_at=incident.opened_at,
            )
            for incident in incidents[:PAGE_SIZE]
        ],
        next_page=page + 1 if has_next_page else None,
    )
