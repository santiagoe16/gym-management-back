from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from app.core.database import get_session
from app.core.deps import get_current_active_user, require_admin, require_trainer_or_admin
from app.models.user import User, UserRole
from app.models.product import Product, ProductCreate, ProductUpdate
from app.models.read_models import ProductRead

router = APIRouter()

@router.get("/", response_model=List[ProductRead])
def read_products(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Get all products - Admin and Trainer access"""
    products = session.exec(select(Product).offset(skip).limit(limit)).all()
    return products

@router.get("/active", response_model=List[ProductRead])
def read_active_products(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Get all active products - Admin and Trainer access"""
    products = session.exec(select(Product).where(Product.is_active == True)).all()
    return products

@router.get("/low-stock", response_model=List[ProductRead])
def read_low_stock_products(
    threshold: int = Query(10, description="Stock threshold for low stock alert"),
    gym_id: Optional[int] = Query(None, description="Filter by gym ID"),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Get products with low stock - Admin and Trainer access only"""
    query = select(Product).where(Product.quantity <= threshold, Product.is_active == True)
    
    # Filter by gym if specified
    if gym_id:
        query = query.where(Product.gym_id == gym_id)
    
    # If trainer, only show products from their gym
    if current_user.role == UserRole.TRAINER:
        query = query.where(Product.gym_id == current_user.gym_id)
    
    products = session.exec(query).all()
    return products

@router.post("/", response_model=ProductRead)
def create_product(
    product: ProductCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin)
):
    """Create a new product - Admin access only"""
    # Check if product with same name already exists
    existing_product = session.exec(select(Product).where(Product.name == product.name)).first()
    if existing_product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product with this name already exists"
        )
    
    db_product = Product.model_validate(product)
    
    session.add(db_product)
    session.commit()
    session.refresh(db_product)
    return db_product

@router.get("/{product_id}", response_model=ProductRead)
def read_product(
    product_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific product - Admin and Trainer access"""
    product = session.exec(select(Product).where(Product.id == product_id)).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.put("/{product_id}", response_model=ProductRead)
def update_product(
    product_id: int,
    product_update: ProductUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin)
):
    """Update a product - Admin access only"""
    db_product = session.exec(select(Product).where(Product.id == product_id)).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Update product data
    product_data = product_update.model_dump(exclude_unset=True)
    for key, value in product_data.items():
        setattr(db_product, key, value)
    
    session.add(db_product)
    session.commit()
    session.refresh(db_product)
    return db_product

@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin)
):
    """Delete a product - Admin access only"""
    db_product = session.exec(select(Product).where(Product.id == product_id)).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    session.delete(db_product)
    session.commit()
    return {"message": "Product deleted successfully"}

@router.put("/{product_id}/stock")
def update_stock(
    product_id: int,
    quantity: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin)
):
    """Update product stock quantity - Admin access only"""
    db_product = session.exec(select(Product).where(Product.id == product_id)).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if quantity < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stock quantity cannot be negative"
        )
    
    db_product.quantity = quantity
    session.add(db_product)
    session.commit()
    session.refresh(db_product)
    return {"message": f"Stock updated to {quantity} units"} 