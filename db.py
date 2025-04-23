import mysql.connector
import pymysql

# Connect to server
cnx = mysql.connector.connect(
    host="127.0.0.1",
    port=3306,
    user="test1",
    password="P@$$w0rd",
    database="Flower_shop_2weit"
)

# Get a cursor
cur = cnx.cursor()
