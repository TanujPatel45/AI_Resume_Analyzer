from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import os

load_dotenv()

DATABASE_URL = (
    f"mysql+pymysql://{os.getenv('DB_USER')}:"
    f"{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:"
    f"{os.getenv('DB_PORT')}/"
    f"{os.getenv('DB_NAME')}"
)

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS resumes (
            id INT PRIMARY KEY AUTO_INCREMENT,
            filename VARCHAR(255),
            analysis LONGTEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))

    conn.commit()

print("Table Created Successfully!")