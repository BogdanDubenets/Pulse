import requests
import json

def test_digest():
    user_id = 461874849
    base_url = "http://localhost:8000/api/v1/digest"
    
    print("\n--- Testing group_by=category ---")
    r_cat = requests.get(f"{base_url}/{user_id}?group_by=category")
    if r_cat.status_code == 200:
        data = r_cat.json()
        print(f"Status: OK")
        print(f"Mode: {data['stats']['mode']}")
        print(f"Categories count: {len(data['categories'])}")
    else:
        print(f"Error: {r_cat.status_code} - {r_cat.text}")

    print("\n--- Testing group_by=time ---")
    r_time = requests.get(f"{base_url}/{user_id}?group_by=time")
    if r_time.status_code == 200:
        data = r_time.json()
        print(f"Status: OK")
        print(f"Mode: {data['stats']['mode']}")
        print(f"Items count: {len(data['items'])}")
        if len(data['items']) > 0:
            print(f"First item type: {data['items'][0]['type']}")
    else:
        print(f"Error: {r_time.status_code} - {r_time.text}")

if __name__ == "__main__":
    test_digest()
