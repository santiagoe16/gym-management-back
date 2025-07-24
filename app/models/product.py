from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime, timezone
from decimal import Decimal

class ProductBase(SQLModel):
    name: str = Field(unique=True, index=True)
    price: Decimal = Field(description="Product price")
    quantity: int = Field(ge=0)  # Number of items in inventory
    gym_id: int = Field(foreign_key="gyms.id", description="Gym where this product is available")
    is_active: bool = True

class Product(ProductBase, table=True):
    __tablename__ = "products"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships
    gym: "Gym" = Relationship(back_populates="products")
    sales: List["Sale"] = Relationship(back_populates="product")

class ProductCreate(ProductBase):
    pass

class ProductUpdate(SQLModel):
    name: Optional[str] = None
    price: Optional[Decimal] = None
    quantity: Optional[int] = None
    gym_id: Optional[int] = None
    is_active: Optional[bool] = None
