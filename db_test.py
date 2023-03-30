from config import db_user, db_password
from mysql.connector import connect, Error


connection = connect(host="localhost", user=db_user, password=db_password)
cur = connection.cursor()
print(connection, cur)
create_db_query = "SHOW DATABASES"

cur.execute(create_db_query)
for i in cur:
    print(i)

