import pytest
from app import app, db
import os

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"postgresql://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}/{os.getenv('TEST_DB_NAME') if app.config.get('TESTING') else os.getenv('DB_NAME')}"
    )
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()

def test_add_person(client):
    response = client.post('/add_person', json={'unique_id': 'testuser', 'phone_number': '1234567890'})
    assert response.status_code == 201
    data = response.get_json()
    assert data['id'] is not None

def test_add_duplicate_person(client):
    client.post('/add_person', json={'unique_id': 'testuser', 'phone_number': '1234567890'})
    response = client.post('/add_person', json={'unique_id': 'testuser', 'phone_number': '9876543210'})
    assert response.status_code == 409
    assert 'already taken' in response.get_json()['error']

def test_add_contact(client):
    client.post('/add_person', json={'unique_id': 'user1', 'phone_number': '1234567890'})
    client.post('/add_person', json={'unique_id': 'user2', 'phone_number': '9876543210'})
    response = client.post('/add_contact', json={'individual_id': 1, 'contact_id': 2, 'contact_date': '2025-03-14'})
    assert response.status_code == 201
    data = response.get_json()
    assert data['id'] is not None

def test_get_contacts(client):
    client.post('/add_person', json={'unique_id': 'user1', 'phone_number': '1234567890'})
    client.post('/add_person', json={'unique_id': 'user2', 'phone_number': '9876543210'})
    client.post('/add_contact', json={'individual_id': 1, 'contact_id': 2, 'contact_date': '2025-03-14'})
    response = client.get('/contacts/user1')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['direct']) == 1
    assert data['direct'][0]['contact_id'] == 2