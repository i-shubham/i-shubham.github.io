from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user, require_role
from app.database import get_db

router = APIRouter(prefix="/api/products", tags=["products"])


def _enrich(product: models.Product, db: Session) -> dict:
    brand = db.query(models.BrandProfile).filter(
        models.BrandProfile.user_id == product.brand_user_id
    ).first()
    return {
        "id": product.id,
        "brand_user_id": product.brand_user_id,
        "title": product.title,
        "description": product.description,
        "category": product.category,
        "budget": float(product.budget),
        "deadline": product.deadline,
        "deliverables": product.deliverables,
        "status": product.status,
        "created_at": product.created_at,
        "brand_name": brand.company if brand else "",
        "brand_logo": brand.logo if brand else "",
    }


@router.get("")
def list_products(db: Session = Depends(get_db)):
    products = db.query(models.Product).order_by(models.Product.created_at.desc()).all()
    return [_enrich(p, db) for p in products]


@router.get("/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    p = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not p:
        raise HTTPException(404, "product not found")
    return _enrich(p, db)


@router.post("", status_code=201)
def create_product(
    req: schemas.CreateProductRequest,
    current_user: models.User = Depends(require_role("brand")),
    db: Session = Depends(get_db),
):
    if not req.title or req.budget <= 0:
        raise HTTPException(400, "title and budget are required")
    p = models.Product(
        brand_user_id=current_user.id,
        title=req.title,
        description=req.description,
        category=req.category,
        budget=req.budget,
        deadline=req.deadline,
        deliverables=req.deliverables,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return _enrich(p, db)
