from enum import Enum
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime
from decimal import Decimal
from app.models.enums import PaymentType
import pytz


class SaleBase(SQLModel):
    product_id: int = Field(foreign_key="products.id")
    quantity: int = Field(gt=0)  # Number of items sold
    unit_price: Decimal = Field(description="Price per unit at time of sale")
    total_amount: Decimal = Field(description="Total amount for this sale")
    sold_by_id: int = Field(foreign_key="users.id")  # Admin or trainer who made the sale
    gym_id: int = Field(foreign_key="gyms.id", description="Gym where the sale was made")
    sale_date: datetime = Field(default_factory=lambda: datetime.now(pytz.timezone('America/Bogota')))
    payment_type: PaymentType = Field(default=PaymentType.CASH)

class Sale(SaleBase, table=True):
    __tablename__ = "sales"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(pytz.timezone('America/Bogota')))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(pytz.timezone('America/Bogota')))
    
    # Relationships
    product: "Product" = Relationship(back_populates="sales")
    sold_by: "User" = Relationship(back_populates="sales")
    gym: "Gym" = Relationship(back_populates="sales")

class SaleCreate(SQLModel):
    product_id: int
    gym_id: Optional[int] = None
    quantity: int
    payment_type: PaymentType

class SaleUpdate(SQLModel):
    payment_type: Optional[PaymentType] = None
    quantity: Optional[int] = None
    unit_price: Optional[Decimal] = None
    sale_date: Optional[datetime] = None
