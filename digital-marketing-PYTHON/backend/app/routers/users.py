from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db

router = APIRouter(prefix="/api", tags=["users"])


@router.get("/me")
def me(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    user_out = schemas.UserOut.model_validate(current_user)
    result = {"user": user_out}

    if current_user.role == "influencer":
        profile = db.query(models.InfluencerProfile).filter(
            models.InfluencerProfile.user_id == current_user.id
        ).first()
        if profile:
            inf = schemas.InfluencerOut.model_validate(profile)
            inf.name = current_user.name
            result["profile"] = inf
    elif current_user.role == "brand":
        profile = db.query(models.BrandProfile).filter(
            models.BrandProfile.user_id == current_user.id
        ).first()
        if profile:
            result["profile"] = schemas.BrandOut.model_validate(profile)

    return result
