from datetime import datetime
from sqlalchemy import (
    BigInteger, Boolean, Column, Float, ForeignKey,
    Integer, Numeric, String, Text, TIMESTAMP
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True)
    role = Column(String(20), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    influencer_profile = relationship("InfluencerProfile", back_populates="user", uselist=False)
    brand_profile = relationship("BrandProfile", back_populates="user", uselist=False)


class InfluencerProfile(Base):
    __tablename__ = "influencer_profiles"

    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    handle = Column(String(100))
    niche = Column(String(100))
    bio = Column(Text, default="")
    location = Column(String(255), default="")
    avatar = Column(String(500), default="")
    insta_url = Column(String(500), default="")
    yt_url = Column(String(500), default="")
    last_synced = Column(TIMESTAMP(timezone=True), nullable=True)
    insta_followers = Column(Integer, default=0)
    insta_top_reel = Column(Integer, default=0)
    yt_subscribers = Column(Integer, default=0)
    yt_top_views = Column(Integer, default=0)
    engagement = Column(Numeric(5, 2), default=0)
    trial_start = Column(TIMESTAMP(timezone=True), server_default=func.now())
    plan = Column(String(20), default="trial")
    plan_type = Column(String(20), default="subscription")
    subscribed_until = Column(TIMESTAMP(timezone=True), nullable=True)

    user = relationship("User", back_populates="influencer_profile")


class BrandProfile(Base):
    __tablename__ = "brand_profiles"

    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    company = Column(String(255), nullable=False)
    industry = Column(String(100), default="")
    website = Column(String(500), default="")
    about = Column(Text, default="")
    logo = Column(String(500), default="")

    user = relationship("User", back_populates="brand_profile")


class Product(Base):
    __tablename__ = "products"

    id = Column(BigInteger, primary_key=True, index=True)
    brand_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    category = Column(String(100), default="")
    budget = Column(Numeric(12, 2), default=0)
    deadline = Column(String(50), default="")
    deliverables = Column(Text, default="")
    status = Column(String(20), default="open")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    bids = relationship("Bid", back_populates="product")


class Bid(Base):
    __tablename__ = "bids"

    id = Column(BigInteger, primary_key=True, index=True)
    product_id = Column(BigInteger, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    influencer_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(12, 2), default=0)
    message = Column(Text, default="")
    status = Column(String(20), default="pending")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    product = relationship("Product", back_populates="bids")
    concept = relationship("Concept", back_populates="bid", uselist=False)


class Concept(Base):
    __tablename__ = "concepts"

    id = Column(BigInteger, primary_key=True, index=True)
    bid_id = Column(BigInteger, ForeignKey("bids.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(BigInteger, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    brand_user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    influencer_user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    concept = Column(Text, default="")
    script = Column(Text, default="")
    deliverables = Column(Text, default="")
    deadline = Column(String(50), default="")
    shared_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    bid = relationship("Bid", back_populates="concept")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(BigInteger, primary_key=True, index=True)
    type = Column(String(50), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    ref_id = Column(BigInteger, default=0)
    gross = Column(Numeric(12, 2), default=0)
    amount = Column(Numeric(12, 2), default=0)
    status = Column(String(20), default="completed")
    note = Column(Text, default="")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
