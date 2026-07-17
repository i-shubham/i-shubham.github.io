from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import require_role
from app.database import get_db

router = APIRouter(prefix="/api", tags=["payments"])


@router.post("/payments", status_code=201)
def record_payment(
    req: schemas.RecordPaymentRequest,
    current_user: models.User = Depends(require_role("brand", "influencer", "admin")),
    db: Session = Depends(get_db),
):
    payment = models.Payment(
        type=req.type,
        user_id=current_user.id,
        ref_id=req.ref_id or 0,
        gross=req.gross,
        amount=req.amount,
        note=req.note or "",
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


@router.post("/subscriptions")
def subscribe(
    req: schemas.SubscribeRequest,
    current_user: models.User = Depends(require_role("influencer")),
    db: Session = Depends(get_db),
):
    profile = db.query(models.InfluencerProfile).filter(
        models.InfluencerProfile.user_id == current_user.id
    ).first()
    if profile:
        profile.plan = "pro"
        profile.plan_type = req.plan_type or "subscription"
        profile.subscribed_until = datetime.utcnow() + timedelta(days=30)

    db.add(models.Payment(
        type="influencer_subscription",
        user_id=current_user.id,
        gross=1499,
        amount=1499,
        note="Creator Pro monthly subscription",
    ))
    db.commit()
    return {"status": "subscribed", "plan": "pro"}
