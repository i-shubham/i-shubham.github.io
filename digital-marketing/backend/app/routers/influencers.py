import math
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user, require_role
from app.database import get_db

router = APIRouter(prefix="/api/influencers", tags=["influencers"])


def _str_hash(s: str) -> int:
    h = 2166136261
    for c in (s or ""):
        h ^= ord(c)
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def _derive_insta(url: str):
    if not url:
        return 0, 0
    h = _str_hash(url)
    return 50000 + (h % 950000), 100000 + (h % 5000000)


def _derive_yt(url: str):
    if not url:
        return 0, 0
    h = _str_hash(url)
    return 10000 + (h % 490000), 50000 + (h % 3000000)


def _sync_stats(db: Session, profile: models.InfluencerProfile):
    insta_followers, insta_top_reel = _derive_insta(profile.insta_url)
    yt_subscribers, yt_top_views = _derive_yt(profile.yt_url)
    combined = (profile.insta_url or "") + (profile.yt_url or "")
    engagement = round(3.0 + (_str_hash(combined) % 50) / 10.0, 1)
    profile.insta_followers = insta_followers
    profile.insta_top_reel = insta_top_reel
    profile.yt_subscribers = yt_subscribers
    profile.yt_top_views = yt_top_views
    profile.engagement = engagement
    profile.last_synced = datetime.utcnow()


@router.get("")
def list_influencers(db: Session = Depends(get_db)):
    profiles = (
        db.query(models.InfluencerProfile)
        .order_by(models.InfluencerProfile.insta_followers.desc())
        .all()
    )
    result = []
    for p in profiles:
        user = db.query(models.User).filter(models.User.id == p.user_id).first()
        result.append({
            "userId": p.user_id,
            "handle": p.handle,
            "niche": p.niche,
            "bio": p.bio,
            "location": p.location,
            "avatar": p.avatar,
            "instaUrl": p.insta_url,
            "ytUrl": p.yt_url,
            "lastSynced": p.last_synced,
            "instaFollowers": p.insta_followers,
            "instaTopReel": p.insta_top_reel,
            "ytSubscribers": p.yt_subscribers,
            "ytTopViews": p.yt_top_views,
            "engagement": float(p.engagement or 0),
            "trialStart": p.trial_start,
            "plan": p.plan,
            "planType": p.plan_type,
            "subscribedUntil": p.subscribed_until,
            "name": user.name if user else "",
        })
    return result


@router.post("/connect")
def connect_social(
    req: schemas.ConnectSocialRequest,
    current_user: models.User = Depends(require_role("influencer")),
    db: Session = Depends(get_db),
):
    profile = db.query(models.InfluencerProfile).filter(
        models.InfluencerProfile.user_id == current_user.id
    ).first()
    if not profile:
        from fastapi import HTTPException
        raise HTTPException(404, "profile not found")

    if req.insta_url:
        profile.insta_url = req.insta_url
    if req.yt_url:
        profile.yt_url = req.yt_url

    _sync_stats(db, profile)
    db.commit()
    return {"status": "connected", "instaFollowers": profile.insta_followers,
            "ytSubscribers": profile.yt_subscribers, "engagement": float(profile.engagement)}


@router.post("/sync")
def sync_stats(
    current_user: models.User = Depends(require_role("influencer")),
    db: Session = Depends(get_db),
):
    profile = db.query(models.InfluencerProfile).filter(
        models.InfluencerProfile.user_id == current_user.id
    ).first()
    if not profile:
        from fastapi import HTTPException
        raise HTTPException(404, "profile not found")

    _sync_stats(db, profile)
    db.commit()
    return {"instaFollowers": profile.insta_followers, "ytSubscribers": profile.yt_subscribers,
            "engagement": float(profile.engagement)}
