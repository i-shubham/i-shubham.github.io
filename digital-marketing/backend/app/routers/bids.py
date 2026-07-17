from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user, require_role
from app.database import get_db

router = APIRouter(prefix="/api", tags=["bids"])


@router.get("/products/{product_id}/bids")
def list_bids(
    product_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bids = (
        db.query(models.Bid)
        .filter(models.Bid.product_id == product_id)
        .order_by(models.Bid.created_at.desc())
        .all()
    )
    result = []
    for b in bids:
        user = db.query(models.User).filter(models.User.id == b.influencer_user_id).first()
        profile = db.query(models.InfluencerProfile).filter(
            models.InfluencerProfile.user_id == b.influencer_user_id
        ).first()
        result.append({
            "id": b.id,
            "product_id": b.product_id,
            "influencer_user_id": b.influencer_user_id,
            "amount": float(b.amount),
            "message": b.message,
            "status": b.status,
            "created_at": b.created_at,
            "influencer_name": user.name if user else "",
            "influencer_handle": profile.handle if profile else "",
            "influencer_avatar": profile.avatar if profile else "",
        })
    return result


@router.post("/products/{product_id}/bids", status_code=201)
def place_bid(
    product_id: int,
    req: schemas.PlaceBidRequest,
    current_user: models.User = Depends(require_role("influencer")),
    db: Session = Depends(get_db),
):
    existing = db.query(models.Bid).filter(
        models.Bid.product_id == product_id,
        models.Bid.influencer_user_id == current_user.id,
    ).first()
    if existing:
        raise HTTPException(409, "you already placed a bid on this campaign")

    bid = models.Bid(
        product_id=product_id,
        influencer_user_id=current_user.id,
        amount=req.amount,
        message=req.message or "",
    )
    db.add(bid)
    db.commit()
    db.refresh(bid)
    return bid


@router.patch("/bids/{bid_id}")
def update_bid_status(
    bid_id: int,
    req: schemas.UpdateBidRequest,
    current_user: models.User = Depends(require_role("brand")),
    db: Session = Depends(get_db),
):
    if req.status not in ("approved", "rejected"):
        raise HTTPException(400, "status must be 'approved' or 'rejected'")

    bid = db.query(models.Bid).filter(models.Bid.id == bid_id).first()
    if not bid:
        raise HTTPException(404, "bid not found")

    bid.status = req.status

    if req.status == "approved":
        # Reject all other pending bids on this product
        db.query(models.Bid).filter(
            models.Bid.product_id == bid.product_id,
            models.Bid.id != bid_id,
            models.Bid.status == "pending",
        ).update({"status": "rejected"})
        # Mark product in-progress
        db.query(models.Product).filter(models.Product.id == bid.product_id).update(
            {"status": "in_progress"}
        )
        # Record brand commission
        product = db.query(models.Product).filter(models.Product.id == bid.product_id).first()
        if product:
            commission = float(bid.amount) * 0.10
            db.add(models.Payment(
                type="brand_commission",
                user_id=current_user.id,
                ref_id=bid.id,
                gross=float(bid.amount),
                amount=commission,
                note="10% platform commission on accepted bid",
            ))

    db.commit()
    return {"status": req.status}


@router.post("/bids/{bid_id}/concept", status_code=201)
def share_concept(
    bid_id: int,
    req: schemas.ShareConceptRequest,
    current_user: models.User = Depends(require_role("brand")),
    db: Session = Depends(get_db),
):
    bid = db.query(models.Bid).filter(models.Bid.id == bid_id).first()
    if not bid:
        raise HTTPException(404, "bid not found")

    concept = models.Concept(
        bid_id=bid_id,
        product_id=bid.product_id,
        brand_user_id=current_user.id,
        influencer_user_id=bid.influencer_user_id,
        concept=req.concept or "",
        script=req.script or "",
        deliverables=req.deliverables or "",
        deadline=req.deadline or "",
    )
    db.add(concept)
    db.commit()
    db.refresh(concept)
    return concept


@router.get("/bids/{bid_id}/concept")
def get_concept(
    bid_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    concept = db.query(models.Concept).filter(models.Concept.bid_id == bid_id).first()
    if not concept:
        raise HTTPException(404, "concept not found")
    return concept
