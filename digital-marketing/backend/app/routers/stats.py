from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models
from app.database import get_db

router = APIRouter(prefix="/api", tags=["stats"])


@router.get("/stats")
def public_stats(db: Session = Depends(get_db)):
    creators = db.query(models.User).filter(models.User.role == "influencer").count()
    brands = db.query(models.User).filter(models.User.role == "brand").count()
    campaigns = db.query(models.Product).count()
    bids = db.query(models.Bid).count()
    approved = db.query(models.Bid).filter(models.Bid.status == "approved").count()
    delivered = db.query(models.Concept).count()

    delivery = 100
    if approved > 0:
        delivery = round((delivered / approved) * 100)

    return {
        "creators": creators,
        "brands": brands,
        "campaigns": campaigns,
        "bids": bids,
        "approved": approved,
        "delivery": delivery,
    }
