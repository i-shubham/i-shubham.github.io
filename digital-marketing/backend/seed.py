#!/usr/bin/env python3
"""Seed demo data into PostgreSQL. Run once after migrations."""
import sys
from datetime import datetime, timedelta

sys.path.insert(0, ".")

import bcrypt
from app.database import SessionLocal

def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
from app import models
from app.routers.influencers import _derive_insta, _derive_yt, _str_hash

db = SessionLocal()


def seed():
    if db.query(models.User).count() > 0:
        print("Database already seeded — truncate first if you want to re-seed.")
        return

    # Admin
    admin = models.User(role="admin", name="Plugg Admin", email="admin@plugg.io",
                        password_hash=hash_password("admin123"))
    db.add(admin)
    db.flush()
    print(f"Created admin: id={admin.id}")

    # Influencers
    influencers_data = [
        ("Aarav Creates", "aaravcreates@demo.io", "aaravcreates", "Tech",
         "https://instagram.com/aaravcreates", "https://youtube.com/@aaravcreates",
         "img/influencers/inf-aarav.png"),
        ("Diya Fashions", "diyafashions@demo.io", "diyafashions", "Fashion",
         "https://instagram.com/diyafashions", "https://youtube.com/@diyafashion",
         "img/influencers/inf-diya.png"),
        ("Rohan Fitness", "rohanfit@demo.io", "rohanfit", "Fitness",
         "https://instagram.com/rohanfit", "",
         "img/influencers/inf-rohan.png"),
        ("Ishita Travels", "ishitatravels@demo.io", "ishitatravels", "Travel",
         "https://instagram.com/ishitatravels", "https://youtube.com/@ishitatravels",
         "img/influencers/inf-ishita.png"),
        ("Kabir Vlogs", "kabirvlogs@demo.io", "kabirvlogs", "Lifestyle",
         "https://instagram.com/kabirvlogs", "https://youtube.com/@kabirvlogs",
         "img/influencers/inf-kabir.png"),
    ]

    inf_users = {}
    for name, email, handle, niche, insta, yt, avatar in influencers_data:
        u = models.User(role="influencer", name=name, email=email,
                        password_hash=hash_password("demo123"))
        db.add(u)
        db.flush()
        insta_followers, insta_top_reel = _derive_insta(insta)
        yt_subscribers, yt_top_views = _derive_yt(yt)
        combined = (insta or "") + (yt or "")
        engagement = round(3.0 + (_str_hash(combined) % 50) / 10.0, 1)
        p = models.InfluencerProfile(
            user_id=u.id, handle=handle, niche=niche, avatar=avatar,
            insta_url=insta, yt_url=yt,
            insta_followers=insta_followers, insta_top_reel=insta_top_reel,
            yt_subscribers=yt_subscribers, yt_top_views=yt_top_views,
            engagement=engagement, last_synced=datetime.utcnow(),
        )
        db.add(p)
        inf_users[handle] = u.id
        print(f"Created influencer: id={u.id} {name} (@{handle})")

    # Brands
    brands_data = [
        ("Nimbus Audio", "nimbusaudio@demo.io", "Nimbus Audio", "Electronics",
         "https://nimbusaudio.com", "img/brands/brand-nimbus.png"),
        ("GreenLeaf Organics", "greenleaf@demo.io", "GreenLeaf Organics", "Health & Beauty",
         "https://greenleaforganics.in", "img/brands/brand-greenleaf.png"),
        ("Lumio Tech", "lumio@demo.io", "Lumio Tech", "Fashion",
         "https://lumio.co", "img/brands/brand-lumio.png"),
    ]

    brand_users = {}
    for name, email, company, industry, website, logo in brands_data:
        u = models.User(role="brand", name=name, email=email,
                        password_hash=hash_password("demo123"))
        db.add(u)
        db.flush()
        b = models.BrandProfile(user_id=u.id, company=company, industry=industry,
                                website=website, logo=logo)
        db.add(b)
        brand_users[company] = u.id
        print(f"Created brand: id={u.id} {company}")

    db.flush()

    # Products
    nimbus_id = brand_users["Nimbus Audio"]
    greenleaf_id = brand_users["GreenLeaf Organics"]

    products_data = [
        (nimbus_id, "Wireless Earbuds Launch", "Promote our new ANC earbuds with an unboxing + review reel", "Tech", 25000, "2025-02-28", "1 Reel (60s) + 3 Stories"),
        (nimbus_id, "Podcast Mic Campaign", "Showcase our USB-C podcast microphone for creators", "Tech", 40000, "2025-03-15", "1 YouTube video (8-12 min)"),
        (greenleaf_id, "Organic Skincare Range", "Feature our new turmeric face serum in a morning routine video", "Beauty", 18000, "2025-02-20", "1 Reel + 1 Story with swipe-up link"),
        (greenleaf_id, "Protein Bar Launch", "Taste-test & review our new vegan protein bars", "Food", 12000, "2025-03-01", "1 YouTube Short + 2 Stories"),
    ]

    product_ids = []
    for brand_uid, title, desc, cat, budget, deadline, deliverables in products_data:
        p = models.Product(brand_user_id=brand_uid, title=title, description=desc,
                           category=cat, budget=budget, deadline=deadline,
                           deliverables=deliverables)
        db.add(p)
        db.flush()
        product_ids.append(p.id)
        print(f"Created product: id={p.id} \"{title}\"")

    # Demo bids
    bids_data = [
        (product_ids[0], inf_users["aaravcreates"], 20000, "My audience is very tech-savvy. Last earbud review hit 1.4M views!"),
        (product_ids[0], inf_users["diyafashions"], 22000, "I can create a lifestyle + unboxing aesthetic reel."),
        (product_ids[2], inf_users["diyafashions"], 15000, "Skincare content is my forte — high engagement on beauty reels!"),
    ]

    for prod_id, inf_uid, amount, msg in bids_data:
        bid = models.Bid(product_id=prod_id, influencer_user_id=inf_uid,
                         amount=amount, message=msg)
        db.add(bid)
        db.flush()
        print(f"Created bid: id={bid.id} on product {prod_id}")

    db.commit()
    print("Seed complete!")


if __name__ == "__main__":
    seed()
    db.close()
