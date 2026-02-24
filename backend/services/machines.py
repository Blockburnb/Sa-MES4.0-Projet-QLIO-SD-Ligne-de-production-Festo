from ..models import MachineReport


def _machine_to_dict(m: MachineReport):
    return {
        "resource_id": getattr(m, 'resource_id', None),
        "timestamp": getattr(m, 'timestamp', None),
        "automatic_mode": getattr(m, 'automatic_mode', None),
        "manual_mode": getattr(m, 'manual_mode', None),
        "busy": getattr(m, 'busy', None),
        "reset": getattr(m, 'reset', None),
        "error_l0": getattr(m, 'error_l0', None),
        "error_l1": getattr(m, 'error_l1', None),
        "error_l2": getattr(m, 'error_l2', None),
        "machine_name": getattr(m, 'machine_name', None),
    }


def get_machines(db):
    rows = db.query(MachineReport).limit(50).all()
    return [_machine_to_dict(r) for r in rows]
