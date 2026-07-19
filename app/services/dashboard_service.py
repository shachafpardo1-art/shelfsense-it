import logging
from decimal import Decimal

from sqlalchemy import and_, case, func
from sqlalchemy.orm import Session

from app.models.item import Item
from app.schemas.dashboard import DashboardSummaryResponse


logger = logging.getLogger("app.dashboard")


def get_dashboard_summary(db: Session) -> DashboardSummaryResponse:
    total_products, total_units, total_inventory_value, low_stock_count, out_of_stock_count = (
        db.query(
            func.count(Item.id),
            func.coalesce(func.sum(Item.quantity), 0),
            func.coalesce(func.sum(Item.quantity * Item.unit_price), 0),
            func.coalesce(
                func.sum(
                    case(
                        (
                            and_(Item.quantity > 0, Item.quantity <= Item.reorder_level),
                            1,
                        ),
                        else_=0,
                    )
                ),
                0,
            ),
            func.coalesce(
                func.sum(
                    case(
                        (Item.quantity == 0, 1),
                        else_=0,
                    )
                ),
                0,
            ),
        )
        .filter(Item.is_active.is_(True))
        .one()
    )

    inventory_value = (
        total_inventory_value
        if isinstance(total_inventory_value, Decimal)
        else Decimal(str(total_inventory_value or 0))
    ).quantize(Decimal("0.01"))

    summary = DashboardSummaryResponse(
        total_products=total_products or 0,
        total_units=total_units or 0,
        total_inventory_value=inventory_value,
        low_stock_count=low_stock_count or 0,
        out_of_stock_count=out_of_stock_count or 0,
    )

    logger.info(
        "Dashboard summary generated operation=get_dashboard_summary total_products=%s low_stock_count=%s out_of_stock_count=%s",
        summary.total_products,
        summary.low_stock_count,
        summary.out_of_stock_count,
    )
    return summary
