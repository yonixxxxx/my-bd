from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy import select

from app.db.config import SessionDep
from app.products.schemas import (
    ProductCreate, ProductUpdate, ProductOut, ProductFilters
)
from app.products.services import (
    create_product, get_product_by_id, get_products,
    update_product, delete_product, hard_delete_product,
    get_products_by_user
)
from app.products.constants import CATEGORIES
from app.products.models import Product
from app.account.deps import get_current_user, get_current_active_user, require_admin
from app.account.models import User

router = APIRouter(prefix="/products", tags=["Products"])




@router.get("/categories", response_model=List[str])
async def get_categories():
    return CATEGORIES


@router.get("/", response_model=List[ProductOut])
async def list_products(
    session: SessionDep,
    category: Optional[str] = Query(None, description="Фильтр по категории"),
    min_price: Optional[float] = Query(None, ge=0, description="Цена от"),
    max_price: Optional[float] = Query(None, ge=0, description="Цена до"),
    in_stock: Optional[bool] = Query(None, description="Только в наличии"),
    search: Optional[str] = Query(None, description="Поиск по названию"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
):

    filters = ProductFilters(
        category=category,
        min_price=min_price,
        max_price=max_price,
        in_stock=in_stock,
        search=search
    )
    return await get_products(session, filters, skip, limit)


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(
    session: SessionDep,
    product_id: int
):

    product = await get_product_by_id(session, product_id)
    if not product or not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return product




@router.post("/", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def create_new_product(
    session: SessionDep,
    product_data: ProductCreate,
    current_user: User = Depends(get_current_active_user)
):

    return await create_product(session, product_data, current_user.id)


@router.put("/{product_id}", response_model=ProductOut)
async def update_existing_product(
    session: SessionDep,
    product_id: int,
    product_data: ProductUpdate,
    current_user: User = Depends(get_current_active_user)
):

    return await update_product(session, product_id, product_data, current_user.id)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_product(
    session: SessionDep,
    product_id: int,
    current_user: User = Depends(get_current_active_user)
):

    await delete_product(session, product_id, current_user.id)
    return None




@router.get("/admin/all", response_model=List[ProductOut])
async def admin_get_all_products(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
    admin: User = Depends(require_admin)
):

    stmt = select(Product).offset(skip).limit(limit)
    result = await session.scalars(stmt)
    return result.all()


@router.delete("/admin/{product_id}/hard", status_code=status.HTTP_204_NO_CONTENT)
async def admin_hard_delete_product(
    session: SessionDep,
    product_id: int,
    admin: User = Depends(require_admin)
):

    await hard_delete_product(session, product_id, admin.id)
    return None


@router.get("/user/me", response_model=List[ProductOut])
async def get_my_products(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user)
):

    return await get_products_by_user(session, current_user.id, skip, limit)