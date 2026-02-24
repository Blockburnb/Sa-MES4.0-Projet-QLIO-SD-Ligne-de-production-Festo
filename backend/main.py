from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from .db import get_db
from .services.orders import get_orders, get_order_by_id, create_order, update_order_status, get_steps_for_order, simulate_step
from .services.machines import get_machines
from .services.kpis import compute_kpis
from . import schemas
from datetime import datetime

app = FastAPI(title="MES4 API")

# enable CORS for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://127.0.0.1", "http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/orders", response_model=list[schemas.OrderOut])
def read_orders(limit: int = 10, start_date: str | None = Query(None), end_date: str | None = Query(None), site: str | None = Query(None), db=Depends(get_db)):
    # parse ISO dates if provided
    sd = None
    ed = None
    try:
        if start_date:
            sd = datetime.fromisoformat(start_date)
        if end_date:
            ed = datetime.fromisoformat(end_date)
    except Exception:
        # ignore parse errors and treat as None
        sd = None
        ed = None
    return get_orders(db, limit=limit, start_date=sd, end_date=ed, site=site)


@app.get("/orders/{order_id}", response_model=schemas.OrderOut)
def read_order(order_id: int, db=Depends(get_db)):
    order = get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.post("/orders", response_model=schemas.OrderOut)
def create_new_order(order_in: schemas.OrderCreate, db=Depends(get_db)):
    return create_order(db, order_in)


@app.put("/orders/{order_id}/status", response_model=schemas.OrderOut)
def put_order_status(order_id: int, status_in: schemas.StatusUpdate, db=Depends(get_db)):
    o = update_order_status(db, order_id, status_in.status)
    if not o:
        raise HTTPException(status_code=404, detail="Order not found")
    return o


@app.get("/orders/{order_id}/steps", response_model=list[schemas.StepOut])
def order_steps(order_id: int, db=Depends(get_db)):
    return get_steps_for_order(db, order_id)


@app.post("/simulate-step", response_model=schemas.StepOut)
def simulate_step_endpoint(req: schemas.SimulateStepRequest, db=Depends(get_db)):
    return simulate_step(db, req.order_id, req.step_name)


@app.get("/machines", response_model=list[schemas.MachineOut])
def read_machines(db=Depends(get_db)):
    return get_machines(db)


# KPI endpoints: compute a standard set of 15 KPIs from available tables
@app.get("/kpis")
def read_kpis(start_date: str | None = Query(None), end_date: str | None = Query(None), site: str | None = Query(None), db=Depends(get_db)):
    sd = None
    ed = None
    try:
        if start_date:
            sd = datetime.fromisoformat(start_date)
        if end_date:
            ed = datetime.fromisoformat(end_date)
    except Exception:
        sd = None
        ed = None
    k = compute_kpis(db, start_date=sd, end_date=ed, site=site)
    return k


@app.get("/kpis/{kpi_name}")
def read_kpi(kpi_name: str, start_date: str | None = Query(None), end_date: str | None = Query(None), site: str | None = Query(None), db=Depends(get_db)):
    sd = None
    ed = None
    try:
        if start_date:
            sd = datetime.fromisoformat(start_date)
        if end_date:
            ed = datetime.fromisoformat(end_date)
    except Exception:
        sd = None
        ed = None
    k = compute_kpis(db, start_date=sd, end_date=ed, site=site)
    if kpi_name not in k:
        raise HTTPException(status_code=404, detail=f"KPI '{kpi_name}' not found")
    return {kpi_name: k[kpi_name]}
