from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


# ── Auth ────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    role: str
    name: str
    email: str
    password: str
    # Influencer
    handle: Optional[str] = ""
    niche: Optional[str] = ""
    insta_url: Optional[str] = ""
    yt_url: Optional[str] = ""
    bio: Optional[str] = ""
    location: Optional[str] = ""
    # Brand
    company: Optional[str] = ""
    industry: Optional[str] = ""
    website: Optional[str] = ""


class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: int
    role: str
    name: str
    email: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    token: str
    user: UserOut


# ── Influencer Profile ──────────────────────────────────────────────────────

class InfluencerOut(BaseModel):
    user_id: int
    handle: Optional[str] = ""
    niche: Optional[str] = ""
    bio: Optional[str] = ""
    location: Optional[str] = ""
    avatar: Optional[str] = ""
    insta_url: Optional[str] = ""
    yt_url: Optional[str] = ""
    last_synced: Optional[datetime] = None
    insta_followers: int = 0
    insta_top_reel: int = 0
    yt_subscribers: int = 0
    yt_top_views: int = 0
    engagement: float = 0
    trial_start: Optional[datetime] = None
    plan: str = "trial"
    plan_type: Optional[str] = "subscription"
    subscribed_until: Optional[datetime] = None
    name: Optional[str] = None

    class Config:
        from_attributes = True


class ConnectSocialRequest(BaseModel):
    insta_url: Optional[str] = ""
    yt_url: Optional[str] = ""


# ── Brand Profile ───────────────────────────────────────────────────────────

class BrandOut(BaseModel):
    user_id: int
    company: str
    industry: Optional[str] = ""
    website: Optional[str] = ""
    about: Optional[str] = ""
    logo: Optional[str] = ""

    class Config:
        from_attributes = True


# ── Products ────────────────────────────────────────────────────────────────

class CreateProductRequest(BaseModel):
    title: str
    description: Optional[str] = ""
    category: Optional[str] = ""
    budget: float
    deadline: Optional[str] = ""
    deliverables: Optional[str] = ""


class ProductOut(BaseModel):
    id: int
    brand_user_id: int
    title: str
    description: Optional[str] = ""
    category: Optional[str] = ""
    budget: float
    deadline: Optional[str] = ""
    deliverables: Optional[str] = ""
    status: str
    created_at: Optional[datetime] = None
    brand_name: Optional[str] = None
    brand_logo: Optional[str] = None

    class Config:
        from_attributes = True


# ── Bids ────────────────────────────────────────────────────────────────────

class PlaceBidRequest(BaseModel):
    amount: float
    message: Optional[str] = ""


class UpdateBidRequest(BaseModel):
    status: str


class BidOut(BaseModel):
    id: int
    product_id: int
    influencer_user_id: int
    amount: float
    message: Optional[str] = ""
    status: str
    created_at: Optional[datetime] = None
    influencer_name: Optional[str] = None
    influencer_handle: Optional[str] = None
    influencer_avatar: Optional[str] = None

    class Config:
        from_attributes = True


# ── Concepts ────────────────────────────────────────────────────────────────

class ShareConceptRequest(BaseModel):
    concept: Optional[str] = ""
    script: Optional[str] = ""
    deliverables: Optional[str] = ""
    deadline: Optional[str] = ""


class ConceptOut(BaseModel):
    id: int
    bid_id: int
    product_id: int
    brand_user_id: int
    influencer_user_id: int
    concept: Optional[str] = ""
    script: Optional[str] = ""
    deliverables: Optional[str] = ""
    deadline: Optional[str] = ""
    shared_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Payments ────────────────────────────────────────────────────────────────

class RecordPaymentRequest(BaseModel):
    type: str
    ref_id: Optional[int] = 0
    gross: float
    amount: float
    note: Optional[str] = ""


class SubscribeRequest(BaseModel):
    plan_type: Optional[str] = "subscription"


class PaymentOut(BaseModel):
    id: int
    type: str
    user_id: int
    ref_id: Optional[int] = 0
    gross: float
    amount: float
    status: str
    note: Optional[str] = ""
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Admin ───────────────────────────────────────────────────────────────────

class AdminRevenue(BaseModel):
    brand_commissions: float
    influencer_subscriptions: float
    influencer_commissions: float
    total_revenue: float
    recent_payments: list[PaymentOut]
