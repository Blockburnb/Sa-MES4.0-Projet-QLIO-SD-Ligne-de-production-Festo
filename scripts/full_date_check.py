# Comprehensive date existence check across key tables
from backend.db import engine
from sqlalchemy import text

tables_to_check = [
    ("tblfinorder", "Start"),
    ("tblboxpos", "CreationDate"),  # guess field name, we'll handle if missing
    ("tblbufferpos", "CreateDate"),
]

with engine.connect() as conn:
    try:
        dbname = conn.execute(text('SELECT DATABASE()')).scalar()
    except Exception:
        dbname = None
    print('Connected database:', dbname)

    for tbl, date_col in tables_to_check:
        print('\n--- Checking table:', tbl, 'date column candidate:', date_col, '---')
        # existence
        try:
            c = conn.execute(text(f"SELECT COUNT(*) FROM {tbl}")).scalar()
            print('Row count:', c)
        except Exception as e:
            print('Table not accessible or does not exist:', e)
            continue

        # try min/max for the candidate column
        try:
            r = conn.execute(text(f"SELECT MIN({date_col}), MAX({date_col}) FROM {tbl} WHERE {date_col} IS NOT NULL")).fetchone()
            print('MIN/MAX ->', r)
        except Exception as e:
            print('Min/Max on', date_col, 'failed:', e)

        # list distinct dates (date-part) if possible
        try:
            q = text(f"SELECT DATE({date_col}) as d, COUNT(*) as c FROM {tbl} WHERE {date_col} IS NOT NULL GROUP BY d ORDER BY d DESC LIMIT 50")
            rows = list(conn.execute(q))
            print('Distinct dates (most recent first):', len(rows))
            for row in rows[:10]:
                print(row)
        except Exception as e:
            print('Distinct date query failed:', e)

        # if no rows found with candidate column, try to introspect columns and find any datetime-like columns
        if c > 0:
            try:
                cols = [r[0] for r in conn.execute(text(f"SHOW COLUMNS FROM {tbl}"))]
                datetime_cols = [col for col in cols if any(k in col.lower() for k in ('date','time','start','stamp'))]
                print('Columns in', tbl, '->', cols)
                print('Datetime-like candidates:', datetime_cols)
            except Exception as e:
                print('SHOW COLUMNS failed:', e)

            # For each candidate, try distinct dates
            for cand in datetime_cols:
                try:
                    q = text(f"SELECT DATE({cand}) as d, COUNT(*) as c FROM {tbl} WHERE {cand} IS NOT NULL GROUP BY d ORDER BY d DESC LIMIT 20")
                    rows = list(conn.execute(q))
                    print(f'-> Candidate {cand}: {len(rows)} distinct dates')
                    for r in rows[:5]:
                        print('   ', r)
                except Exception as e:
                    print('   Candidate', cand, 'failed:', e)

    # Also dump few sample rows for tblfinorder recent dates
    try:
        print('\n--- Sample recent tblfinorder rows (limit 20) ---')
        q = text('SELECT ONo, Start, End, State FROM tblfinorder ORDER BY Start DESC LIMIT 20')
        for r in conn.execute(q):
            print(dict(r))
    except Exception as e:
        print('Sample query failed:', e)

print('\nFull date check completed')
