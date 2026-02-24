from backend.db import engine
from sqlalchemy import text

with engine.connect() as conn:
    res = conn.execute(text('SELECT * FROM tblfinorder LIMIT 5'))
    cols = res.keys()
    print('COLUMNS:', cols)
    for row in res:
        print(dict(zip(cols, row)))
