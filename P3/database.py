import sqlite3

con = sqlite3.connect('example.db')
cur = con.cursor()
cur.execute('''CREATE TABLE IF NOT EXISTS users
				(name text PRIMARY KEY, password text)''')
if not cur.execute('SELECT * FROM users WHERE name=(?)', ('lucas',)).fetchall():
	cur.execute("INSERT INTO users VALUES ('lucas','12341234')")
# for row in cur.execute('SELECT * FROM users'):
# 		print(f"{row}")
con.commit()
con.close()