import os
import uuid
import hashlib
from dotenv import load_dotenv

import psycopg
from psycopg.rows import dict_row


# Load environment variables from .env
load_dotenv()

# Database config
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")


def get_connection():
    """
    Create and return a PostgreSQL connection
    """
    print(psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        row_factory=dict_row,
        sslmode="require",
        connect_timeout=5))
    return psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        row_factory=dict_row,
        sslmode="require",
        connect_timeout=5
    )


def hash_password(password: str) -> str:
    """
    Hash password using SHA256
    (For production, replace with bcrypt)
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def signup_user(username: str, email: str, password: str):
    """
    Create a new user account

    Returns:
        dict -> user data if success
        None -> if failed
    """
    user_id = str(uuid.uuid4())
    hashed_pw = hash_password(password)

    conn = None
    
    try:
        conn = get_connection()
        print(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (user_id, username, email, password)
                VALUES (%s, %s, %s, %s)
                RETURNING user_id, username, email
                """,
                (user_id, username, email, hashed_pw)
            )

            user = cur.fetchone()
            conn.commit()
            return user

    except psycopg.errors.UniqueViolation as e:
        if conn:
            conn.rollback()
        print("❌ Email already exists", e)
        return None

    except Exception as e:
        if conn:
            conn.rollback()
        print("❌ Signup error:", e)
        return None

    finally:
        if conn:
            conn.close()


def login_user(email: str, password: str):
    """
    Authenticate user

    Returns:
        dict -> user data if valid
        None -> if invalid
    """
    hashed_pw = hash_password(password)

    conn = None

    try:
        conn = get_connection()

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT user_id, username, email
                FROM users
                WHERE email = %s AND password = %s
                """,
                (email, hashed_pw)
            )

            return cur.fetchone()

    except Exception as e:
        print("❌ Login error:", e)
        return None

    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    print("Testing DB connection...")

    try:
        conn = get_connection()
        print("✅ Connected to database")
        conn.close()
    except Exception as e:
        print("❌ Connection failed:", e)
