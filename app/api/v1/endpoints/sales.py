from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select, func
from sqlalchemy.orm import selectinload
from app.core.database import get_session
from app.core.deps import require_admin, require_trainer_or_admin
from app.models.user import User, UserRole
from app.models.product import Product
from app.models.sale import Sale, SaleCreate, SaleUpdate
from datetime import date
from app.models.read_models import SaleRead

router = APIRouter()

trainer_message_view = "You can only view sales for users in your gym"
trainer_message_create = "You can only create sales for users in your gym"

@router.post("/", response_model=SaleRead)
def create_sale(
    sale: SaleCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Create a new sale - Admin and Trainer access (both can sell products)"""
    
    query = select( Product ).options( 
        selectinload( Product.gym ) 
    ).where( Product.id == sale.product_id, Product.is_active == True )

    if( current_user.role == UserRole.TRAINER ):
        query = query.where( Product.gym_id == current_user.gym_id )
    else:
        query = query.where( Product.gym_id == sale.gym_id )

    product = session.exec( query ).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or inactive"
        )
    
    # Check if there's enough stock
    if product.quantity < sale.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient stock. Available: {product.quantity}, Requested: {sale.quantity}"
        )
    
    # Calculate total amount
    total_amount = product.price * sale.quantity
    
    # Create sale record with all required fields
    sale_data = sale.model_dump()
    sale_data.update({
        "total_amount": total_amount,
        "sold_by_id": current_user.id,
        "gym_id": current_user.gym_id,
        "unit_price": product.price
    })
    
    db_sale = Sale.model_validate(sale_data)
    
    # Update product stock
    product.quantity -= sale.quantity
    
    session.add(db_sale)
    session.add(product)
    session.commit()
    session.refresh(db_sale)

    return_data = SaleRead.model_validate(db_sale)
    return_data.gym = product.gym
    return_data.sold_by = current_user
    
    return db_sale

@router.get("/", response_model=List[SaleRead])
def read_sales(
    skip: int = 0,
    limit: int = 100,
    trainer_id: Optional[int] = Query(None, description="Filter by trainer ID"),
    product_id: Optional[int] = Query(None, description="Filter by product ID"),
    start_date: Optional[date] = Query(None, description="Filter sales from this date"),
    end_date: Optional[date] = Query(None, description="Filter sales until this date"),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Get all sales with filters - Admin can see all, Trainer sees only their own"""
    query = select(Sale).options(selectinload(Sale.product), selectinload(Sale.sold_by), selectinload(Sale.gym))
    
    # Apply filters
    if trainer_id:
        query = query.where(Sale.sold_by_id == trainer_id)
    if product_id:
        query = query.where(Sale.product_id == product_id)
    if start_date:
        query = query.where(func.date(Sale.sale_date) >= start_date)
    if end_date:
        query = query.where(func.date(Sale.sale_date) <= end_date)
    
    # If trainer, only show their own sales. Admin can see all sales.
    if current_user.role == UserRole.TRAINER:
        query = query.where(Sale.sold_by_id == current_user.id)
    
    sales = session.exec(query.offset(skip).limit(limit)).all()
    
    return sales

@router.get("/daily", response_model=List[SaleRead])
def read_daily_sales(
    sale_date: date = Query(..., description="Date to get sales for"),
    trainer_id: Optional[int] = Query(None, description="Filter by trainer ID"),
    gym_id: Optional[int] = Query(None, description="Filter by gym ID"),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Get sales for a specific date - Admin can see all, Trainer sees only their own"""
    query = select(Sale).options(selectinload(Sale.product), selectinload(Sale.sold_by), selectinload(Sale.gym)).where(func.date(Sale.sale_date) == sale_date)
    
    if trainer_id:
        query = query.where( Sale.sold_by_id == trainer_id )
    
    if gym_id:
        query = query.where( Sale.gym_id == gym_id )
    
    if current_user.role == UserRole.TRAINER:
        query = query.where( Sale.sold_by_id == current_user.id )
    
    sales = session.exec( query ).all()
    
    return sales

@router.get("/summary")
def get_sales_summary(
    start_date: Optional[date] = Query(None, description="Start date for summary"),
    end_date: Optional[date] = Query(None, description="End date for summary"),
    trainer_id: Optional[int] = Query(None, description="Filter by trainer ID"),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Get sales summary - Admin can see all, Trainer sees only their own"""
    query = select(Sale).options(selectinload(Sale.product), selectinload(Sale.sold_by), selectinload(Sale.gym))
    
    # Apply filters
    if start_date:
        query = query.where(func.date(Sale.sale_date) >= start_date)
    if end_date:
        query = query.where(func.date(Sale.sale_date) <= end_date)
    if trainer_id:
        query = query.where(Sale.sold_by_id == trainer_id)
    
    # If trainer, only show their own sales. Admin can see all sales.
    if current_user.role == UserRole.TRAINER:
        query = query.where(Sale.sold_by_id == current_user.id)
    
    sales = session.exec(query).all()
    
    total_sales = len(sales)
    total_revenue = sum(sale.total_amount for sale in sales)
    total_items = sum(sale.quantity for sale in sales)

    # Group sales by product to get product details and quantities
    product_summary = {}
    for sale in sales:
        if sale.product:
            product_id = sale.product.id
            if product_id not in product_summary:
                product_summary[product_id] = {
                    "product_id": product_id,
                    "product_name": sale.product.name,
                    "product_price": float(sale.product.price),
                    "total_quantity_sold": 0,
                    "total_revenue": 0,
                    "number_of_sales": 0
                }
            
            product_summary[product_id]["total_quantity_sold"] += sale.quantity
            product_summary[product_id]["total_revenue"] += float(sale.total_amount)
            product_summary[product_id]["number_of_sales"] += 1
    
    # Convert to list and sort by total revenue (descending)
    product_details = list(product_summary.values())
    product_details.sort(key=lambda x: x["total_revenue"], reverse=True)
    
    return {
        "total_sales": total_sales,
        "total_revenue": float(total_revenue),
        "total_items_sold": total_items,
        "product_summary": product_details,
        "period": {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None
        }
    }

@router.get("/{sale_id}", response_model=SaleRead)
def read_sale(
    sale_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Get a specific sale - Admin can see all, Trainer sees only their own"""
    sale = session.exec(select(Sale).options(selectinload(Sale.product), selectinload(Sale.sold_by), selectinload(Sale.gym)).where(Sale.id == sale_id)).first()
    if sale is None:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    # If trainer, only allow access to their own sales. Admin can see all sales.
    if current_user.role == UserRole.TRAINER and sale.sold_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own sales"
        )
    
    return sale

@router.put("/{sale_id}", response_model=SaleRead)
def update_sale(
    sale_id: int,
    sale_update: SaleUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin)
):
    """Update a sale - Admin access only"""
    db_sale = session.exec(select(Sale).where(Sale.id == sale_id)).first()
    if db_sale is None:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    # Update sale data
    sale_data = sale_update.model_dump(exclude_unset=True)
    for key, value in sale_data.items():
        setattr(db_sale, key, value)
    
    # Recalculate total amount if quantity or unit_price changed
    if 'quantity' in sale_data or 'unit_price' in sale_data:
        db_sale.total_amount = db_sale.unit_price * db_sale.quantity
    
    session.add(db_sale)
    session.commit()
    session.refresh(db_sale)
    return db_sale

@router.delete("/{sale_id}")
def delete_sale(
    sale_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin)
):
    """Delete a sale - Admin access only"""
    db_sale = session.exec(select(Sale).where(Sale.id == sale_id)).first()
    if db_sale is None:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    # Restore product stock
    product = session.exec(select(Product).where(Product.id == db_sale.product_id)).first()
    if product:
        product.quantity += db_sale.quantity
        session.add(product)
    
    session.delete(db_sale)
    session.commit()
    return {"message": "Sale deleted successfully"} 