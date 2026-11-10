"""Mobile alert subscriptions."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from incidentdesk.db import get_session
from incidentdesk.models import AlertSubscription, Service

router = APIRouter(prefix="/mobile/v1/subscriptions", tags=["mobile subscriptions"])


class SubscriptionIn(BaseModel):
    engineer: str
    services: list[str]
    min_priority: Literal["P1", "P2", "P3", "P4"]


class SubscriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    engineer: str
    services: list[str]
    min_priority: str


@router.post("", response_model=SubscriptionOut, status_code=201)
def create_subscription(body: SubscriptionIn, session: Session = Depends(get_session)):
    available = set(session.scalars(select(Service.slug).where(Service.slug.in_(body.services))))
    unknown = [slug for slug in body.services if slug not in available]
    if unknown:
        raise HTTPException(422, f"Unknown service(s): {', '.join(unknown)}")

    subscription = AlertSubscription(
        engineer=body.engineer,
        services=body.services,
        min_priority=body.min_priority,
    )
    session.add(subscription)
    session.commit()
    session.refresh(subscription)
    return subscription


@router.get("", response_model=list[SubscriptionOut])
def list_subscriptions(engineer: str, session: Session = Depends(get_session)):
    query = select(AlertSubscription).where(AlertSubscription.engineer == engineer).order_by(AlertSubscription.id)
    return list(session.scalars(query))
