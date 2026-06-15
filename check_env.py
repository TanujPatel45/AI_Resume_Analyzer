from dotenv import load_dotenv
import os

load_dotenv()

print("HOST =", os.getenv("DB_HOST"))
print("PORT =", os.getenv("DB_PORT"))
print("USER =", os.getenv("DB_USER"))
print("DATABASE =", os.getenv("DB_NAME"))