from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.products.models import Product
from app.products.schemas import ProductCreate, ProductUpdate, ProductFilters
from app.account.models import User


async def create_product(
    session: AsyncSession,
    product_data: ProductCreate,
    user_id: int
) -> Product:

    new_product = Product(
        name=product_data.name,
        description=product_data.description,
        price=product_data.price,
        stock=0,
        category=product_data.category,

        image_url=str(product_data.image_url) if product_data.image_url else None,
        location=product_data.location,
        created_by=user_id
    )
    session.add(new_product)
    await session.commit()
    await session.refresh(new_product)
    return new_product


async def get_product_by_id(session: AsyncSession, product_id: int) -> Product | None:

    stmt = select(Product).where(Product.id == product_id)
    result = await session.scalars(stmt)
    return result.first()


async def get_products(
    session: AsyncSession,
    filters: ProductFilters | None = None,
    skip: int = 0,
    limit: int = 100
) -> list[Product]:

    stmt = select(Product).where(Product.is_active == True)

    if filters:
        if filters.category:
            stmt = stmt.where(Product.category == filters.category)
        if filters.min_price:
            stmt = stmt.where(Product.price >= filters.min_price)
        if filters.max_price:
            stmt = stmt.where(Product.price <= filters.max_price)
        if filters.in_stock:

            stmt = stmt.where(Product.stock > 0)
        if filters.search:
            stmt = stmt.where(
                or_(
                    Product.name.ilike(f"%{filters.search}%"),
                    Product.description.ilike(f"%{filters.search}%")
                )
            )

    stmt = stmt.offset(skip).limit(limit)
    result = await session.scalars(stmt)
    return result.all()


async def update_product(
    session: AsyncSession,
    product_id: int,
    product_data: ProductUpdate,
    user_id: int
) -> Product:

    product = await get_product_by_id(session, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Товар не найден"
        )


    user = await session.get(User, user_id)
    if product.created_by != user_id and not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав на обновление этого продукта."
        )

    update_data = product_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    await session.commit()
    await session.refresh(product)
    return product


async def delete_product(
    session: AsyncSession,
    product_id: int,
    user_id: int
) -> bool:

    product = await get_product_by_id(session, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Товар не найден"
        )

    user = await session.get(User, user_id)
    if product.created_by != user_id and not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав на удаление этого товара."
        )

    product.is_active = False
    await session.commit()
    return True


async def hard_delete_product(
    session: AsyncSession,
    product_id: int,
    user_id: int
) -> bool:

    product = await get_product_by_id(session, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Товар не найден"
        )

    user = await session.get(User, user_id)
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только администратор может безвозвратно удалять товары."
        )

    await session.delete(product)
    await session.commit()
    return True


async def get_products_by_user(
    session: AsyncSession,
    user_id: int,
    skip: int = 0,
    limit: int = 100
) -> list[Product]:

    stmt = select(Product).where(
        Product.created_by == user_id,
        Product.is_active == True
    ).offset(skip).limit(limit)
    result = await session.scalars(stmt)
    return result.all()