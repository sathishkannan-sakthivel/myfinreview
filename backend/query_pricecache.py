import sqlite3

conn = sqlite3.connect('finreview.db')
cur = conn.cursor()

try:
    cur.execute('SELECT count(*) FROM PriceCache')
    print('Rows:', cur.fetchone()[0])
    cur.execute('SELECT * FROM PriceCache LIMIT 5')
    for row in cur.fetchall():
        print(row)
except Exception as e:
    print('Error:', e)
finally:
    conn.close()
