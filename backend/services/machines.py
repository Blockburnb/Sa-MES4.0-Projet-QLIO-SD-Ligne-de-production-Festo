from ..models import MachineReport


def get_machines(db):
    return db.query(MachineReport).all()
