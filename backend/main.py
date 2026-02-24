from fastapi import FastAPI, Depends, HTTPException
from .db import get_db
from .services.orders import get_orders, get_order_by_id

app = FastAPI(title="MES4 API")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/orders")
def read_orders(limit: int = 10, db=Depends(get_db)):
    return get_orders(db, limit)


@app.get("/orders/{order_id}")
def read_order(order_id: int, db=Depends(get_db)):
    order = get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
