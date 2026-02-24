# Quick DB inspection script — prints columns for target tables using information_schema
from backend.db import engine
from sqlalchemy import text

print('Using engine.url ->', getattr(engine, 'url', None))

try:
    with engine.connect() as conn:
        try:
            dbname = conn.execute(text('SELECT DATABASE()')).scalar()
        except Exception:
            dbname = None
        print('Current database:', dbname)

        # list tables
        try:
            tables = [r[0] for r in conn.execute(text('SHOW TABLES')).all()]
        except Exception as e:
            print('SHOW TABLES failed ->', e)
            tables = []
        print('Found', len(tables), 'tables')

        def describe_via_info(tbl):
            print('\n---', tbl, '---')
            try:
                q = text("SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_KEY FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = :schema AND TABLE_NAME = :tbl ORDER BY ORDINAL_POSITION")
                for row in conn.execute(q, {'schema': dbname, 'tbl': tbl}):
                    print(row)
            except Exception as e:
                print('information_schema query failed for', tbl, '->', e)

        for t in ('tblfinorder', 'tblfinstep', 'tblmachinereport'):
            describe_via_info(t)

except Exception as e:
    print('Connection failed ->', e)
