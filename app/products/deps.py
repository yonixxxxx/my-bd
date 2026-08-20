from fastapi import Depends, HTTPException, status

from app.db.config import SessionDep
from app.account.models import User
from app.account.deps import get_current_active_user
from app.products.services import get_product_by_id


async def check_product_owner(
        session: SessionDep,
        product_id: int,
        current_user: User = Depends(get_current_active_user)
) -> int:

    product = await get_product_by_id(session, product_id)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Товар не найден"
        )


    if product.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав для редактирования или удаления этого товара"
        )

    return product_id