from database.db_connection import get_schema
from database.db_connection import run_query

print(get_schema())

print("\n---------------------------\n")

query = "SELECT * FROM Customer LIMIT 5;"

result = run_query(query)

print(result)