from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select, func
from app.core.database import get_session
from app.core.deps import require_admin, require_trainer_or_admin
from app.models.user import User, UserRole
from app.models.product import Product
from app.models.sale import Sale, SaleCreate, SaleUpdate
from datetime import date
from app.models.read_models import SaleRead

router = APIRouter()

@router.post("/", response_model=SaleRead)
def create_sale(
    sale: SaleCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Create a new sale - Admin and Trainer access (both can sell products)"""
    # Verify product exists and is active
    product = session.exec(select(Product).where(Product.id == sale.product_id, Product.is_active == True)).first()
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
        "unit_price": sale.unit_price or product.price
    })
    
    db_sale = Sale.model_validate(sale_data)
    
    # Update product stock
    product.quantity -= sale.quantity
    
    session.add(db_sale)
    session.add(product)
    session.commit()
    session.refresh(db_sale)
    
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
    query = select(Sale)
    
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
    
    # Add product and trainer names
    result = []
    for sale in sales:
        sale_dict = sale.model_dump()
        sale_dict["product_name"] = sale.product.name if sale.product else None
        sale_dict["trainer_name"] = sale.sold_by.full_name if sale.sold_by else None
        result.append(SaleReadWithDetails(**sale_dict))
    
    return result

@router.get("/daily", response_model=List[SaleRead])
def read_daily_sales(
    sale_date: date = Query(..., description="Date to get sales for"),
    trainer_id: Optional[int] = Query(None, description="Filter by trainer ID"),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Get sales for a specific date - Admin can see all, Trainer sees only their own"""
    query = select(Sale).where(func.date(Sale.sale_date) == sale_date)
    
    if trainer_id:
        query = query.where(Sale.sold_by_id == trainer_id)
    
    # If trainer, only show their own sales. Admin can see all sales.
    if current_user.role == UserRole.TRAINER:
        query = query.where(Sale.sold_by_id == current_user.id)
    
    sales = session.exec(query).all()
    
    # Add product and trainer names
    result = []
    for sale in sales:
        sale_dict = sale.model_dump()
        sale_dict["product_name"] = sale.product.name if sale.product else None
        sale_dict["trainer_name"] = sale.sold_by.full_name if sale.sold_by else None
        result.append(SaleReadWithDetails(**sale_dict))
    
    return result

@router.get("/summary")
def get_sales_summary(
    start_date: Optional[date] = Query(None, description="Start date for summary"),
    end_date: Optional[date] = Query(None, description="End date for summary"),
    trainer_id: Optional[int] = Query(None, description="Filter by trainer ID"),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Get sales summary - Admin can see all, Trainer sees only their own"""
    query = select(Sale)
    
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
    
    return {
        "total_sales": total_sales,
        "total_revenue": float(total_revenue),
        "total_items_sold": total_items,
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
    sale = session.exec(select(Sale).where(Sale.id == sale_id)).first()
    if sale is None:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    # If trainer, only allow access to their own sales. Admin can see all sales.
    if current_user.role == UserRole.TRAINER and sale.sold_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own sales"
        )
    
    sale_dict = sale.model_dump()
    sale_dict["product_name"] = sale.product.name if sale.product else None
    sale_dict["trainer_name"] = sale.sold_by.full_name if sale.sold_by else None
    
    return SaleRead(**sale_dict)

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