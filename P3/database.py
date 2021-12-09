import sqlite3

con = sqlite3.connect('example.db')
cur = con.cursor()
cur.execute('''CREATE TABLE IF NOT EXISTS users
				(name text PRIMARY KEY, password text)''')
# for row in cur.execute('SELECT * FROM users'):
# 		print(f"{row}")
con.commit()
con.close()