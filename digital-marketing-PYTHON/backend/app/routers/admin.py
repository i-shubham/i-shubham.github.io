from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import require_role
from app.database import get_db

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/revenue")
def admin_revenue(
    current_user: models.User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    def sum_type(t):
        r = db.query(func.sum(models.Payment.amount)).filter(
            models.Payment.type == t, models.Payment.status == "completed"
        ).scalar()
        return float(r or 0)

    brand_commissions = sum_type("brand_commission")
    inf_subscriptions = sum_type("influencer_subscription")
    inf_commissions = sum_type("influencer_commission")

    recent = (
        db.query(models.Payment)
        .order_by(models.Payment.created_at.desc())
        .limit(20)
        .all()
    )

    return {
        "brand_commissions": brand_commissions,
        "influencer_subscriptions": inf_subscriptions,
        "influencer_commissions": inf_commissions,
        "total_revenue": brand_commissions + inf_subscriptions + inf_commissions,
        "recent_payments": recent,
    }
