from ..models import FinOrder


def get_orders(db, limit: int = 10):
    return db.query(FinOrder).limit(limit).all()


def get_order_by_id(db, order_id: int):
    return db.query(FinOrder).filter(FinOrder.id == order_id).first()
