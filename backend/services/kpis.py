from datetime import datetime
from sqlalchemy import text

# Best-effort KPI computations using available MES4 tables. Functions are resilient to
# missing tables/columns and return None for KPIs that cannot be computed.

def _table_exists(conn, tbl):
    try:
        r = conn.execute(text(f"SHOW TABLES LIKE :t"), {"t": tbl}).fetchone()
        return r is not None
    except Exception:
        return False


def _get_columns(conn, tbl):
    try:
        rows = conn.execute(text(f"SHOW COLUMNS FROM {tbl}")).fetchall()
        return [r[0] for r in rows]
    except Exception:
        return []


def _safe_scalar(conn, sql, params=None):
    try:
        return conn.execute(text(sql), params or {}).scalar()
    except Exception:
        return None


def compute_kpis(db, start_date: datetime | None = None, end_date: datetime | None = None, site: str | None = None):
    conn = db.connection() if hasattr(db, 'connection') else db
    # If SQLAlchemy Session has execute, use it directly
    if hasattr(db, 'execute') and not hasattr(db, 'connection'):
        conn = db

    # build WHERE clause for time filtering for tables that use a timestamp/date column
    where_clauses = []
    params = {}
    if start_date is not None:
        where_clauses.append("{col} >= :start_date")
        params['start_date'] = start_date
    if end_date is not None:
        where_clauses.append("{col} <= :end_date")
        params['end_date'] = end_date

    # Default KPI structure
    kpis = {
        "production_count": None,
        "throughput_per_day": None,
        "average_cycle_time_min": None,
        "average_lead_time_min": None,
        "buffer_occupancy_avg": None,
        "buffer_movements": None,
        "machine_availability_pct": None,
        "machine_utilization_pct": None,
        "error_rate_pct": None,
        "scrap_rate_pct": None,
        "yield_pct": None,
        "defect_rate_pct": None,
        "mttr_minutes": None,
        "mtbf_minutes": None,
        "energy_consumption_kwh": None,
    }

    # 1) production_count: prefer tblboxpos, fallback to tblfinorder
    try:
        if _table_exists(conn, 'tblboxpos'):
            cnt = _safe_scalar(conn, "SELECT COUNT(*) FROM tblboxpos")
            kpis['production_count'] = int(cnt) if cnt is not None else None
        elif _table_exists(conn, 'tblfinorder'):
            cond = ''
            if start_date is not None and end_date is not None:
                cond = "WHERE Start BETWEEN :start_date AND :end_date"
            cnt = _safe_scalar(conn, f"SELECT COUNT(*) FROM tblfinorder {cond}", params)
            kpis['production_count'] = int(cnt) if cnt is not None else None
    except Exception:
        pass

    # Helper: compute days in range
    days = None
    if start_date is not None and end_date is not None:
        delta = end_date - start_date
        days = max(delta.days, 1)

    # 2) throughput_per_day
    try:
        if kpis['production_count'] is not None and days:
            kpis['throughput_per_day'] = round(kpis['production_count'] / days, 3)
    except Exception:
        pass

    # 3) average_cycle_time (tblfinorder: avg(End-Start))
    try:
        if _table_exists(conn, 'tblfinorder'):
            q = "SELECT AVG(TIMESTAMPDIFF(SECOND, Start, End)) FROM tblfinorder WHERE Start IS NOT NULL AND End IS NOT NULL"
            if start_date is not None and end_date is not None:
                q = q + " AND Start BETWEEN :start_date AND :end_date"
            secs = _safe_scalar(conn, q, params)
            if secs is not None:
                kpis['average_cycle_time_min'] = round(secs / 60.0, 2)
    except Exception:
        pass

    # 4) average_lead_time (PlannedStart -> End)
    try:
        if _table_exists(conn, 'tblfinorder'):
            q = "SELECT AVG(TIMESTAMPDIFF(SECOND, PlannedStart, End)) FROM tblfinorder WHERE PlannedStart IS NOT NULL AND End IS NOT NULL"
            if start_date is not None and end_date is not None:
                q = q + " AND PlannedStart BETWEEN :start_date AND :end_date"
            secs = _safe_scalar(conn, q, params)
            if secs is not None:
                kpis['average_lead_time_min'] = round(secs / 60.0, 2)
    except Exception:
        pass

    # 5 & 6) buffer occupancy & movements (tblbufferpos)
    try:
        if _table_exists(conn, 'tblbufferpos'):
            # average occupancy per day: count rows grouped by DATE(TimeStamp)
            q = "SELECT AVG(c) FROM (SELECT DATE(TimeStamp) d, COUNT(*) c FROM tblbufferpos WHERE TimeStamp IS NOT NULL GROUP BY DATE(TimeStamp)) x"
            if start_date is not None and end_date is not None:
                q = "SELECT AVG(c) FROM (SELECT DATE(TimeStamp) d, COUNT(*) c FROM tblbufferpos WHERE TimeStamp BETWEEN :start_date AND :end_date GROUP BY DATE(TimeStamp)) x"
            occ = _safe_scalar(conn, q, params)
            if occ is not None:
                kpis['buffer_occupancy_avg'] = round(float(occ), 2)
            # movements = total rows in range
            q2 = "SELECT COUNT(*) FROM tblbufferpos"
            if start_date is not None and end_date is not None:
                q2 = "SELECT COUNT(*) FROM tblbufferpos WHERE TimeStamp BETWEEN :start_date AND :end_date"
            mv = _safe_scalar(conn, q2, params)
            if mv is not None:
                kpis['buffer_movements'] = int(mv)
    except Exception:
        pass

    # 7 & 8) machine availability & utilization (tblmachinereport)
    try:
        if _table_exists(conn, 'tblmachinereport'):
            total_q = "SELECT COUNT(*) FROM tblmachinereport"
            busy_q = "SELECT COUNT(*) FROM tblmachinereport WHERE Busy = 1"
            err_q = "SELECT COUNT(*) FROM tblmachinereport WHERE (ErrorL0 = 1 OR ErrorL1 = 1 OR ErrorL2 = 1)"
            if start_date is not None and end_date is not None:
                total_q += " WHERE TimeStamp BETWEEN :start_date AND :end_date"
                busy_q += " AND TimeStamp BETWEEN :start_date AND :end_date" if "WHERE" in busy_q else " WHERE TimeStamp BETWEEN :start_date AND :end_date"
                err_q += " AND TimeStamp BETWEEN :start_date AND :end_date" if "WHERE" in err_q else " WHERE TimeStamp BETWEEN :start_date AND :end_date"
            total = _safe_scalar(conn, total_q, params) or 0
            busy = _safe_scalar(conn, busy_q, params) or 0
            errs = _safe_scalar(conn, err_q, params) or 0
            if total > 0:
                kpis['machine_utilization_pct'] = round(100.0 * busy / total, 2)
                kpis['machine_availability_pct'] = round(100.0 * (1 - (errs / total)), 2)
                kpis['error_rate_pct'] = round(100.0 * errs / total, 3)
    except Exception:
        pass

    # 9-12) quality metrics from tblboxpos if available
    try:
        if _table_exists(conn, 'tblboxpos'):
            cols = _get_columns(conn, 'tblboxpos')
            # possible column for conformity
            conform_col = None
            for c in cols:
                if c.lower() in ('conform', 'isconform', 'is_ok', 'isok', 'ok', 'good', 'conforme'):
                    conform_col = c
                    break
            # possible scrap/defect indicator
            defect_col = None
            for c in cols:
                if c.lower() in ('defect', 'scrap', 'isdefect', 'ng', 'nok'):
                    defect_col = c
                    break
            total_boxes_q = "SELECT COUNT(*) FROM tblboxpos"
            if start_date is not None and end_date is not None and 'TimeStamp' in cols:
                total_boxes_q = "SELECT COUNT(*) FROM tblboxpos WHERE TimeStamp BETWEEN :start_date AND :end_date"
            total_boxes = _safe_scalar(conn, total_boxes_q, params) or 0
            if total_boxes > 0 and conform_col:
                good_q = f"SELECT COUNT(*) FROM tblboxpos WHERE {conform_col} IN (1,'1', 'true', 'True')"
                if start_date is not None and end_date is not None and 'TimeStamp' in cols:
                    good_q += " AND TimeStamp BETWEEN :start_date AND :end_date"
                good = _safe_scalar(conn, good_q, params) or 0
                kpis['yield_pct'] = round(100.0 * good / total_boxes, 2)
                kpis['scrap_rate_pct'] = round(100.0 * (1 - good / total_boxes), 2)
            elif total_boxes > 0 and defect_col:
                defect_q = f"SELECT COUNT(*) FROM tblboxpos WHERE {defect_col} IN (1,'1','true')"
                if start_date is not None and end_date is not None and 'TimeStamp' in cols:
                    defect_q += " AND TimeStamp BETWEEN :start_date AND :end_date"
                defects = _safe_scalar(conn, defect_q, params) or 0
                kpis['defect_rate_pct'] = round(100.0 * defects / total_boxes, 2)
    except Exception:
        pass

    # 13 & 14) crude MTTR/MTBF approximations from tblmachinereport errors timestamps
    try:
        if _table_exists(conn, 'tblmachinereport'):
            # find transitions error->noerror and noerror->error per resource
            q = "SELECT ResourceID, TimeStamp, (ErrorL0 OR ErrorL1 OR ErrorL2) as has_err FROM tblmachinereport ORDER BY ResourceID, TimeStamp"
            rows = conn.execute(text(q)).fetchall()
            # compute simple up/down durations per resource
            from collections import defaultdict
            prev = {}
            down_times = []
            up_times = []
            for r in rows:
                rid = r[0]
                ts = r[1]
                has_err = bool(r[2])
                if rid in prev:
                    p_has, p_ts = prev[rid]
                    # if previous was error and now not -> transition to up (repair)
                    if p_has and not has_err:
                        down_times.append((ts - p_ts).total_seconds())
                    # if previous was OK and now error -> transition to down (failure)
                    if not p_has and has_err:
                        up_times.append((ts - p_ts).total_seconds())
                prev[rid] = (has_err, ts)
            if down_times:
                kpis['mttr_minutes'] = round(sum(down_times) / len(down_times) / 60.0, 2)
            if up_times:
                kpis['mtbf_minutes'] = round(sum(up_times) / len(up_times) / 60.0, 2)
    except Exception:
        pass

    # 15) energy consumption: try dataEnergy or robotino_data.csv presence
    try:
        if _table_exists(conn, 'dataEnergy'):
            q = "SELECT SUM(Energy_kWh) FROM dataEnergy"
            if start_date is not None and end_date is not None:
                q += " WHERE TimeStamp BETWEEN :start_date AND :end_date"
            e = _safe_scalar(conn, q, params)
            if e is not None:
                kpis['energy_consumption_kwh'] = float(e)
    except Exception:
        pass

    return kpis
