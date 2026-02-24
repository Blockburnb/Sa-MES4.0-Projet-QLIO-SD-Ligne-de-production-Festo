from ..models import FinOrder, FinStep
from datetime import datetime


def _order_to_dict(o: FinOrder):
    return {
        "id": getattr(o, "id", None),
        "name": getattr(o, "name", None),
        "status": getattr(o, "status", None),
        "created_at": getattr(o, "created_at", None),
    }


def _step_to_dict(s: FinStep):
    return {
        "id": getattr(s, "id", None),
        "order_id": getattr(s, "order_id", None),
        "step_name": getattr(s, "step_name", None),
        "status": getattr(s, "status", None),
        "started_at": getattr(s, "started_at", None),
        "finished_at": getattr(s, "finished_at", None),
    }


def get_orders(db, limit: int = 10, start_date: datetime | None = None, end_date: datetime | None = None, site: str | None = None):
    q = db.query(FinOrder)
    # Filter by start date (Start column) if provided
    if start_date is not None:
        try:
            q = q.filter(getattr(FinOrder, 'start') >= start_date)
        except Exception:
            pass
    if end_date is not None:
        try:
            q = q.filter(getattr(FinOrder, 'start') <= end_date)
        except Exception:
            pass
    # Note: 'site' mapping not available in schema; ignore if provided
    rows = q.order_by(getattr(FinOrder, 'id')).limit(limit).all()
    return [_order_to_dict(r) for r in rows]


def get_order_by_id(db, order_id: int):
    r = db.query(FinOrder).filter(getattr(FinOrder, 'id') == order_id).first()
    if not r:
        return None
    return _order_to_dict(r)


def create_order(db, order_data):
    o = FinOrder()
    o.name = order_data.name
    o.status = order_data.status or 'new'
    o.created_at = datetime.now()
    db.add(o)
    db.commit()
    db.refresh(o)
    return _order_to_dict(o)


def update_order_status(db, order_id: int, new_status: str):
    o = db.query(FinOrder).filter(getattr(FinOrder, 'id') == order_id).first()
    if not o:
        return None
    o.status = new_status
    db.commit()
    db.refresh(o)
    return _order_to_dict(o)


def get_steps_for_order(db, order_id: int):
    rows = db.query(FinStep).filter(getattr(FinStep, 'order_id') == order_id).all()
    return [_step_to_dict(r) for r in rows]


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
    return _step_to_dict(s)
