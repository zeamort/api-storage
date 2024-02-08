import mysql.connector

conn = mysql.connector.connect(host="localhost", user="python", 
password="python", database="events")

c = conn.cursor()
c.execute('''
          DROP TABLE power_usage, location
          ''')

conn.commit()
conn.close()
