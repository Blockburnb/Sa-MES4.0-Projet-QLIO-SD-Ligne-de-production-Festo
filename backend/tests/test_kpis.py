from fastapi.testclient import TestClient
from backend.main import app
from datetime import datetime

client = TestClient(app)

EXPECTED_KPIS = {
    "production_count",
    "throughput_per_day",
    "average_cycle_time_min",
    "average_lead_time_min",
    "buffer_occupancy_avg",
    "buffer_movements",
    "machine_availability_pct",
    "machine_utilization_pct",
    "error_rate_pct",
    "scrap_rate_pct",
    "yield_pct",
    "defect_rate_pct",
    "mttr_minutes",
    "mtbf_minutes",
    "energy_consumption_kwh",
}


def _is_number(v):
    return isinstance(v, (int, float))


def test_get_kpis_structure():
    r = client.get('/kpis')
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)
    # ensure all expected KPI keys are present
    assert EXPECTED_KPIS.issubset(set(data.keys()))
    # values must be either None or numeric
    for k in EXPECTED_KPIS:
        v = data.get(k)
        assert v is None or _is_number(v)


def test_get_single_kpi_valid():
    r = client.get('/kpis/production_count')
    assert r.status_code == 200
    data = r.json()
    assert 'production_count' in data
    assert data['production_count'] is None or isinstance(data['production_count'], int)


def test_get_single_kpi_invalid():
    r = client.get('/kpis/not_a_kpi')
    assert r.status_code == 404


def test_kpis_with_date_range_consistency():
    # wide range to increase chance of data being present
    sd = '2016-01-01T00:00:00'
    ed = '2025-12-31T23:59:59'
    r = client.get(f'/kpis?start_date={sd}&end_date={ed}')
    assert r.status_code == 200
    data = r.json()
    assert EXPECTED_KPIS.issubset(set(data.keys()))

    prod = data.get('production_count')
    thr = data.get('throughput_per_day')
    try:
        sd_dt = datetime.fromisoformat(sd)
        ed_dt = datetime.fromisoformat(ed)
        days = max((ed_dt - sd_dt).days, 1)
    except Exception:
        days = None

    # If both production_count and throughput_per_day are numbers, they should be consistent
    if prod is not None and thr is not None and days:
        # throughput is production / days (rounded to 3 decimals in service)
        expected = round(prod / days, 3)
        assert abs(expected - thr) < 0.001


def test_kpis_invalid_date_param_are_tolerated():
    r = client.get('/kpis?start_date=not-a-date')
    # endpoint should tolerate parse errors and still return 200
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)
    # still contains KPI keys
    assert EXPECTED_KPIS.issubset(set(data.keys()))
