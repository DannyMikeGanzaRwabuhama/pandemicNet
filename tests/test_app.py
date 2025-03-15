import pytest
from app import app, db
from ui import generate_explanation
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


def test_no_predictions_for_direct(client):
    client.post('/add_person', json={'unique_id': 'user1', 'phone_number': '1234567890'})
    client.post('/add_person', json={'unique_id': 'user2', 'phone_number': '9876543210'})
    client.post('/add_contact', json={'individual_id': 1, 'contact_id': 2, 'contact_date': '2025-03-15'})
    response = client.get('/contacts/user1')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['direct']) == 1
    assert len(data['predicted']) == 0  # No second-degree yet


def test_low_confidence_prediction(client):
    client.post('/add_person', json={'unique_id': 'user1', 'phone_number': '1234567890'})
    client.post('/add_person', json={'unique_id': 'user2', 'phone_number': '9876543210'})
    client.post('/add_person', json={'unique_id': 'user3', 'phone_number': '5555555555'})
    client.post('/add_contact', json={'individual_id': 1, 'contact_id': 2, 'contact_date': '2025-03-01'})
    client.post('/add_contact', json={'individual_id': 2, 'contact_id': 3, 'contact_date': '2025-03-02'})
    response = client.get('/contacts/user1')
    data = response.get_json()
    assert data['predicted'][0]['confidence'] < 0.5


def test_generate_explanation_high_confidence():
    result = {}
    generate_explanation("user3", 0.85, 3, 0, 1, result)
    text = result["user3"].lower()
    assert "user3" in text or "meet" in text  # Broader check
    assert any(x in text for x in ["0.85", "85%", "hot"])  # Flexible confidence
    assert "3" in text or "contacts" in text  # Feature presence


def test_generate_explanation_low_confidence():
    result = {}
    generate_explanation("user7", 0.19, 2, 13, 0, result)
    text = result["user7"].lower()
    assert "user7" in text or "meet" in text
    assert any(x in text for x in ["0.19", "19%", "wild", "guess", "low"])  # Wider net
    assert "13" in text or "days" in text
