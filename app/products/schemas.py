from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator
from app.products.constants import CATEGORIES




class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    stock: int = Field(default=0, ge=0)
    category: Optional[str] = Field(None, max_length=100)
    image_url: Optional[str] = Field(None, max_length=500)

    @validator("category")
    def validate_category(cls, v):
        if v and v not in CATEGORIES:
            raise ValueError(f"Категория должна быть одной из: {', '.join(CATEGORIES)}")
        return v


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    category: Optional[str] = Field(None, max_length=100)
    image_url: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None

    @validator("category")
    def validate_category(cls, v):
        if v and v not in CATEGORIES:
            raise ValueError(f"Категория должна быть одной из: {', '.join(CATEGORIES)}")
        return v


class ProductOut(ProductBase):
    id: int
    is_active: bool
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}



class ProductFilters(BaseModel):
    category: Optional[str] = None
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    in_stock: Optional[bool] = None
    search: Optional[str] = None