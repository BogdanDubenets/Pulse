import os
import requests
from dotenv import load_dotenv

load_dotenv()

def check():
    url = f"{os.getenv('SUPABASE_URL')}/rest/v1/users?id=eq.461874849&select=*"
    headers = {
        'apikey': os.getenv('SUPABASE_SERVICE_ROLE_KEY'),
        'Authorization': f"Bearer {os.getenv('SUPABASE_SERVICE_ROLE_KEY')}"
    }
    r = requests.get(url, headers=headers)
    print("User Data:", r.json())

    # Also check subscriptions
    sub_url = f"{os.getenv('SUPABASE_URL')}/rest/v1/user_subscriptions?user_id=eq.461874849&select=*,channels(*)"
    r_sub = requests.get(sub_url, headers=headers)
    print("\nSubscriptions:", r_sub.json())

if __name__ == "__main__":
    check()
