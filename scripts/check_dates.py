# Script to list distinct Start dates in tblfinorder and sample rows for the two most recent dates
from backend.db import engine
from sqlalchemy import text

with engine.connect() as conn:
    print('Connected to', conn.execute(text('SELECT DATABASE()')).scalar())

    # Get distinct dates and counts
    q = text("SELECT DATE(Start) as d, COUNT(*) as cnt FROM tblfinorder GROUP BY d ORDER BY d DESC LIMIT 50")
    print('\nDistinct dates (most recent first):')
    dates = []
    for row in conn.execute(q):
        print(row)
        dates.append(str(row['d']))

    if not dates:
        print('\nNo dates found in tblfinorder START column.')
    else:
        # take the two most recent dates
        recent = dates[:2]
        print('\nTwo most recent dates:', recent)
        for d in recent:
            print(f"\nRows for date {d}: (limit 10)")
            q2 = text("SELECT ONo, Start, End, State FROM tblfinorder WHERE DATE(Start) = :d LIMIT 10")
            for r in conn.execute(q2, {'d': d}):
                print(dict(r))
