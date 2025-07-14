import psycopg2

conn = psycopg2.connect(database="template1",
                        host="localhost",
                        user="postgres",
                        password="nikhil",
                        port="5432")
print("Connect")
cursor = conn.cursor()
print("Execute")
cursor.execute("SHOW TABLES")
print(cursor.fetchall())
