from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import hash_password, verify_password, create_access_token
from app.database import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=schemas.LoginResponse, status_code=201)
def register(req: schemas.RegisterRequest, db: Session = Depends(get_db)):
    if req.role not in ("influencer", "brand"):
        raise HTTPException(400, "role must be 'influencer' or 'brand'")
    if db.query(models.User).filter(models.User.email == req.email).first():
        raise HTTPException(409, "email already registered")

    user = models.User(
        role=req.role,
        name=req.name,
        email=req.email,
        password_hash=hash_password(req.password),
    )
    db.add(user)
    db.flush()

    if req.role == "influencer":
        db.add(models.InfluencerProfile(
            user_id=user.id,
            handle=req.handle or req.name.replace(" ", "").lower(),
            niche=req.niche or "Lifestyle",
            insta_url=req.insta_url or "",
            yt_url=req.yt_url or "",
            bio=req.bio or "",
            location=req.location or "",
        ))
    else:
        db.add(models.BrandProfile(
            user_id=user.id,
            company=req.company or req.name,
            industry=req.industry or "General",
            website=req.website or "",
        ))

    db.commit()
    db.refresh(user)
    token = create_access_token(user.id, user.role, user.name)
    return schemas.LoginResponse(token=token, user=schemas.UserOut.model_validate(user))


@router.post("/login", response_model=schemas.LoginResponse)
def login(req: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == req.email).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(401, "invalid email or password")
    token = create_access_token(user.id, user.role, user.name)
    return schemas.LoginResponse(token=token, user=schemas.UserOut.model_validate(user))
