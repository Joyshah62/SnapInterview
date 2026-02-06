from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)


def signup_user(email, password, username):
    """Sign up in Supabase Auth and create a row in users table"""
    print(email, password, username)

    res = supabase.auth.sign_up({
        "email": email,
        "password": password
    })

    if res.user is None:
        return None, res

    user_id = res.user.id  # Supabase UID

    # Insert into users table
    insert_res = supabase.table("users").insert({
        "user_id": user_id,
        "username": username
    }).execute()

    return res.user, insert_res


def login_user(email, password):
    """Login via Supabase Auth and fetch user row"""
    res = supabase.auth.sign_in_with_password({
        "email": email,
        "password": password
    })

    if res.user is None:
        return None

    # Fetch user row by user_id
    user_row = supabase.table("users").select("*").eq("user_id", res.user.id).execute()
    if user_row.data:
        return user_row.data[0]
    return None
