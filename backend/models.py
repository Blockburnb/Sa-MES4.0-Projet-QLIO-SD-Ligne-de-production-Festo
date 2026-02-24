from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Boolean

Base = declarative_base()


class FinOrder(Base):
    """Model mapped to existing tblfinorder table in MES4.
    Important: column names reflect the actual DB (ONo is the order PK).
    Compatibility properties provide the attributes the rest of the code expects.
    """
    __tablename__ = "tblfinorder"

    # real DB columns
    id = Column("ONo", Integer, primary_key=True)
    planned_start = Column("PlannedStart", DateTime)
    planned_end = Column("PlannedEnd", DateTime)
    start = Column("Start", DateTime)
    end = Column("End", DateTime)
    cno = Column("CNo", Integer)
    state = Column("State", Integer)
    enabled = Column("Enabled", Boolean)
    release = Column("Release", DateTime)

    # Compatibility attributes expected by services / schemas
    @property
    def name(self):
        # There is no OrderName column in this schema; provide a human-friendly name
        return f"Order-{self.id}" if self.id is not None else None

    @property
    def status(self):
        # State is numeric in the DB; present as string to keep compatibility
        return str(self.state) if self.state is not None else None

    @property
    def created_at(self):
        # Use the Start timestamp as a best-effort creation date
        return self.start


class FinStep(Base):
    """Model mapped to tblfinstep. The table uses a composite PK (StepNo, ONo, OPos).
    Provide convenience attributes used by the existing services.
    """
    __tablename__ = "tblfinstep"

    wp_no = Column("WPNo", Integer)
    step_no = Column("StepNo", Integer, primary_key=True)
    order_no = Column("ONo", Integer, primary_key=True)
    opos = Column("OPos", Integer, primary_key=True)
    description = Column("Description", String(255))
    op_no = Column("OpNo", Integer)
    next_step_no = Column("NextStepNo", Integer)
    first_step = Column("FirstStep", Boolean)
    planned_start = Column("PlannedStart", DateTime)
    planned_end = Column("PlannedEnd", DateTime)
    start = Column("Start", DateTime)
    end = Column("End", DateTime)
    resource_id = Column("ResourceID", Integer)
    active = Column("Active", Boolean)

    # Compatibility attributes expected by services
    @property
    def id(self):
        # synthesize a simple id from composite key
        return f"{self.order_no}-{self.step_no}-{self.opos}"

    @property
    def order_id(self):
        return self.order_no

    @property
    def step_name(self):
        return self.description

    @property
    def status(self):
        # No explicit textual status column; infer from End/Active
        if self.end is not None:
            return "done"
        if self.active is False:
            return "pending"
        return "in_progress"

    @property
    def started_at(self):
        return self.start

    @property
    def finished_at(self):
        return self.end


class MachineReport(Base):
    """Model mapped to tblmachinereport. Primary keys include ResourceID and TimeStamp
    (and also ID is present). Expose a machine_name property for compatibility.
    """
    __tablename__ = "tblmachinereport"

    resource_id = Column("ResourceID", Integer, primary_key=True)
    timestamp = Column("TimeStamp", DateTime, primary_key=True)
    automatic_mode = Column("AutomaticMode", Boolean)
    manual_mode = Column("ManualMode", Boolean)
    busy = Column("Busy", Boolean)
    reset = Column("Reset", Boolean)
    error_l0 = Column("ErrorL0", Boolean)
    error_l1 = Column("ErrorL1", Boolean)
    error_l2 = Column("ErrorL2", Boolean)
    id = Column("ID", Integer, primary_key=True)

    @property
    def machine_name(self):
        return f"Resource-{self.resource_id}" if self.resource_id is not None else None


__all__ = ["Base", "FinOrder", "FinStep", "MachineReport"]
