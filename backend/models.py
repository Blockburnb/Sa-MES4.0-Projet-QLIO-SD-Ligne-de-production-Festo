from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime

Base = declarative_base()


class FinOrder(Base):
    __tablename__ = "tblfinorder"

    id = Column("ID", Integer, primary_key=True)
    name = Column("OrderName", String(255))
    status = Column("Status", String(50))
    created_at = Column("CreateDate", DateTime)


class FinStep(Base):
    __tablename__ = "tblfinstep"

    id = Column("ID", Integer, primary_key=True)
    order_id = Column("OrderID", Integer)
    step_name = Column("StepName", String(255))
    status = Column("Status", String(50))
    started_at = Column("StartDate", DateTime)
    finished_at = Column("EndDate", DateTime)


class MachineReport(Base):
    __tablename__ = "tblmachinereport"

    id = Column("ID", Integer, primary_key=True)
    machine_name = Column("MachineName", String(255))
    report = Column("Report", String(1000))
    created_at = Column("CreateDate", DateTime)
