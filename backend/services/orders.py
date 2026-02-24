from ..models import FinOrder, FinStep
from datetime import datetime


def get_orders(db, limit: int = 10):
    return db.query(FinOrder).limit(limit).all()


def get_order_by_id(db, order_id: int):
    return db.query(FinOrder).filter(FinOrder.id == order_id).first()


def create_order(db, order_data):
    o = FinOrder()
    o.name = order_data.name
    o.status = order_data.status or 'new'
    o.created_at = datetime.now()
    db.add(o)
    db.commit()
    db.refresh(o)
    return o


def update_order_status(db, order_id: int, new_status: str):
    o = get_order_by_id(db, order_id)
    if not o:
        return None
    o.status = new_status
    db.commit()
    db.refresh(o)
    return o


def get_steps_for_order(db, order_id: int):
    return db.query(FinStep).filter(FinStep.order_id == order_id).all()


def simulate_step(db, order_id: int, step_name: str):
    s = FinStep()
    s.order_id = order_id
    s.step_name = step_name
    s.status = 'done'
    s.started_at = datetime.now()
    s.finished_at = datetime.now()
    db.add(s)
    db.commit()
    db.refresh(s)
    return s
