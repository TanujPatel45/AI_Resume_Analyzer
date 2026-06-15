import bcrypt
from sqlalchemy import text

def hash_password(password):
    return bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    ).decode()

def verify_password(password, hashed):
    return bcrypt.checkpw(
        password.encode(),
        hashed.encode()
    )

def register_user(engine, username, email, password):

    hashed_password = hash_password(password)

    with engine.connect() as conn:

        conn.execute(
            text("""
            INSERT INTO users
            (username,email,password)
            VALUES
            (:username,:email,:password)
            """),
            {
                "username": username,
                "email": email,
                "password": hashed_password
            }
        )

        conn.commit()

def login_user(engine, email, password):

    with engine.connect() as conn:

        result = conn.execute(
            text("""
            SELECT password
            FROM users
            WHERE email=:email
            """),
            {"email": email}
        )

        user = result.fetchone()

        if user:
            return verify_password(
                password,
                user[0]
            )

    return False