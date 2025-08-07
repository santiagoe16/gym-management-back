from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime, timezone
from decimal import Decimal

from app.models.auth import PaymentType

class SaleBase(SQLModel):
    product_id: int = Field(foreign_key="products.id")
    quantity: int = Field(gt=0)  # Number of items sold
    unit_price: Decimal = Field(description="Price per unit at time of sale")
    total_amount: Decimal = Field(description="Total amount for this sale")
    sold_by_id: int = Field(foreign_key="users.id")  # Admin or trainer who made the sale
    gym_id: int = Field(foreign_key="gyms.id", description="Gym where the sale was made")
    sale_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payment_type: PaymentType = Field(default=PaymentType.CASH)

class Sale(SaleBase, table=True):
    __tablename__ = "sales"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships
    product: "Product" = Relationship(back_populates="sales")
    sold_by: "User" = Relationship(back_populates="sales")
    gym: "Gym" = Relationship(back_populates="sales")

class SaleCreate(SQLModel):
    product_id: int
    gym_id: Optional[int] = None
    quantity: int

class SaleUpdate(SQLModel):
    quantity: Optional[int] = None
    unit_price: Optional[Decimal] = None
    sale_date: Optional[datetime] = None
