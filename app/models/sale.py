from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime
from decimal import Decimal

class SaleBase(SQLModel):
    product_id: int = Field(foreign_key="products.id")
    quantity: int = Field(gt=0)  # Number of items sold
    unit_price: Decimal = Field(max_digits=10, decimal_places=2)  # Price per unit at time of sale
    total_amount: Decimal = Field(max_digits=10, decimal_places=2)  # Total amount for this sale
    sold_by_id: int = Field(foreign_key="users.id")  # Trainer who made the sale
    gym_id: int = Field(foreign_key="gyms.id", description="Gym where the sale occurred")
    sale_date: datetime = Field(default_factory=datetime.utcnow)

class Sale(SaleBase, table=True):
    __tablename__ = "sales"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    product: Optional["Product"] = Relationship(back_populates="sales")
    sold_by: Optional["User"] = Relationship(back_populates="sales")
    gym: "Gym" = Relationship(back_populates="sales")

class SaleCreate(SQLModel):
    product_id: int
    quantity: int
    unit_price: Optional[Decimal] = None  # If not provided, will use product's current price

class SaleUpdate(SQLModel):
    quantity: Optional[int] = None
    unit_price: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    gym_id: Optional[int] = None
    sale_date: Optional[datetime] = None

class SaleRead(SaleBase):
    id: int
    created_at: datetime
    updated_at: datetime

class SaleReadWithDetails(SaleRead):
    product_name: Optional[str] = None
    trainer_name: Optional[str] = None 