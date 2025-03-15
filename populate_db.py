import random
from datetime import datetime, timedelta
import requests

BASE_URL = "http://localhost:5000"

# Users
users = [f"user{i}" for i in range(1, 11)]
phone_numbers = [f"12345678{i:02d}" for i in range(1, 11)]

# Add users, skip if exists
user_ids = {}
for uid, phone in zip(users, phone_numbers):
    response = requests.post(f"{BASE_URL}/add_person", json={"unique_id": uid, "phone_number": phone})
    if response.status_code == 201:
        print(f"Added {uid}: {response.status_code}")
    elif response.status_code == 409:
        print(f"{uid} already exists: {response.status_code}")
    # Fetch ID
    fetch = requests.get(f"{BASE_URL}/person/{uid}")
    if fetch.status_code == 200:
        user_ids[uid] = fetch.json()['id']
    else:
        print(f"Failed to fetch {uid}: {fetch.status_code}")
print("User IDs:", user_ids)

# Generate contacts
start_date = datetime(2025, 3, 1)

contacts = [
    # Strong (high confidence)
    {"individual_id": "user1", "contact_id": "user2", "contact_date": "2025-03-15"},
    {"individual_id": "user2", "contact_id": "user3", "contact_date": "2025-03-15"},
    {"individual_id": "user2", "contact_id": "user4", "contact_date": "2025-03-14"},
    # Weak (low confidence)
    {"individual_id": "user5", "contact_id": "user6", "contact_date": "2025-03-01"},  # Old
    {"individual_id": "user6", "contact_id": "user7", "contact_date": "2025-03-02"},
    {"individual_id": "user8", "contact_id": "user9", "contact_date": "2025-03-10"}  # Sparse
]
for _ in range(14):
    ind = random.choice(users)
    cont = random.choice([u for u in users if u != ind])
    days_ago = random.randint(0, 14)
    contact_date = (start_date + timedelta(days=days_ago)).strftime("%Y-%m-%d")
    contacts.append({"individual_id": ind, "contact_id": cont, "contact_date": contact_date})

# Add contacts
for contact in contacts:
    ind_id = user_ids.get(contact['individual_id'])
    cont_id = user_ids.get(contact['contact_id'])
    if ind_id and cont_id:
        response = requests.post(
            f"{BASE_URL}/add_contact",
            json={"individual_id": ind_id, "contact_id": cont_id, "contact_date": contact['contact_date']}
        )
        print(
            f"Added contact {contact['individual_id']} -> {contact['contact_id']} "
            f"on {contact['contact_date']}: {response.status_code}")
    else:
        print(f"Skipped contact {contact['individual_id']} -> {contact['contact_id']}—missing ID")

print("Database populated!")
