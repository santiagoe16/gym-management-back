from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from app.core.database import get_session
from app.core.deps import get_current_active_user, require_admin, require_trainer_or_admin
from app.core.methods import check_trainer_gym
from app.models.gym import Gym
from app.models.user import User, UserRole
from app.models.product import Product, ProductCreate, ProductUpdate
from app.models.read_models import ProductRead

router = APIRouter()

trainer_message = "You can only view products for users in your gym"

@router.get("/", response_model=List[ProductRead])
def read_products(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Get all products - Admin and Trainer access"""
    query = select(Product).options(selectinload(Product.gym)).offset(skip).limit(limit)

    if current_user.role == UserRole.TRAINER:
        query = query.where(Product.gym_id == current_user.gym_id)

    products = session.exec(query).all()

    return products

@router.get( "/active", response_model = List[ ProductRead ] )
def read_active_products(
    session: Session = Depends( get_session ),
    current_user: User = Depends( get_current_active_user )
):
    """Get all active products - Admin and Trainer access"""
    query = select( Product ).options( selectinload( Product.gym ) ).where( Product.is_active == True )

    if current_user.role == UserRole.TRAINER:
        query = query.where( Product.gym_id == current_user.gym_id )

    products = session.exec( query ).all()

    return products

@router.get("/low-stock", response_model=List[ProductRead])
def read_low_stock_products(
    threshold: int = Query(10, description="Stock threshold for low stock alert"),
    gym_id: Optional[int] = Query(None, description="Filter by gym ID"),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Get products with low stock - Admin and Trainer access only"""
    query = select(Product).options(selectinload(Product.gym)).where(Product.quantity <= threshold, Product.is_active == True)
    
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
    existing_product = session.exec( select( Product ).where( Product.name == product.name, Product.gym_id == product.gym_id ) ).first()

    if existing_product:
        return existing_product
    
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
    product = session.exec(select(Product).options(selectinload(Product.gym)).where(Product.id == product_id)).first()

    if product is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    check_trainer_gym( product.gym_id, current_user, trainer_message )

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
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    if product_update.name:
        existing_product = session.exec( select( Product ).where( Product.name == product_update.name, Product.gym_id == db_product.gym_id ) ).first()
        
        if existing_product:
            raise HTTPException( status_code = 404, detail=  "Ya existe un producto con este nombre" )
    
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
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    session.delete(db_product)
    session.commit()
    return {"message": "Producto eliminado exitosamente"}

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
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    if quantity < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cantidad de stock no puede ser negativa"
        )
    
    if quantity > 999999999:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cantidad de stock no puede exceder 999,999,999"
        )
    
    db_product.quantity = quantity
    session.add(db_product)
    session.commit()
    session.refresh(db_product)
    return {"message": f"Stock actualizado a {quantity} unidades"} 