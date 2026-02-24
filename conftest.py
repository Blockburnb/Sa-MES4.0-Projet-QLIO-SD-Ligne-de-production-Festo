import pathlib


def pytest_ignore_collect(path):
    """Ignore any top-level test_*.py files outside the backend/tests folder.
    This workspace contains auxiliary test scripts; we only want backend/tests collected.
    """
    p = pathlib.Path(str(path))
    if p.name.startswith("test_"):
        # allow files under backend/tests
        try:
            if any(part == 'backend' for part in p.parts) and any(part == 'tests' for part in p.parts):
                return False
        except Exception:
            pass
        return True
    return False
