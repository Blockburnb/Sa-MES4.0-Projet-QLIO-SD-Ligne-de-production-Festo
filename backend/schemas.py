from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class OrderBase(BaseModel):
    name: str
    status: Optional[str] = None


class OrderCreate(OrderBase):
    pass


class OrderOut(OrderBase):
    id: int
    created_at: Optional[datetime]

    class Config:
        orm_mode = True


class StepBase(BaseModel):
    order_id: int
    step_name: str
    status: Optional[str] = None


class StepCreate(StepBase):
    pass


class StepOut(StepBase):
    id: int
    started_at: Optional[datetime]
    finished_at: Optional[datetime]

    class Config:
        orm_mode = True


class MachineOut(BaseModel):
    machine_name: str
    report: Optional[str] = None
    created_at: Optional[datetime]

    class Config:
        orm_mode = True


class StatusUpdate(BaseModel):
    status: str


class SimulateStepRequest(BaseModel):
    order_id: int
    step_name: str
