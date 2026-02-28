import os
import requests
from dotenv import load_dotenv

def main():
    load_dotenv()
    
    supabase_url = "https://irjqhaxbinyczgyfndzc.supabase.co"
    api_key = os.getenv('SUPABASE_ANON_KEY')
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    headers = {
        'apikey': api_key,
        'Authorization': f'Bearer {service_key}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
    }
    
    # query user_subscriptions and join channels
    url = f"{supabase_url}/rest/v1/user_subscriptions?user_id=eq.461874849&select=channel_id,channels(id,username,title,is_active,last_scanned_at,posts_count_24h)"
    
    response = requests.get(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data)} subscriptions for user 461874849:")
        for idx, sub in enumerate(data):
            ch = sub.get('channels', {})
            print(f"{idx+1}. @{ch.get('username')} | {ch.get('title')} | Active: {ch.get('is_active')} | Scanned: {ch.get('last_scanned_at')} | Posts(24h): {ch.get('posts_count_24h')}")
    else:
        print("Error:", response.text)

if __name__ == "__main__":
    main()
