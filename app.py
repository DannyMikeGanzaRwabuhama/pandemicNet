from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import re
import networkx as nx
from datetime import datetime
from dotenv import load_dotenv
import os
import pickle
import numpy as np

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"postgresql://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}/{os.getenv('TEST_DB_NAME') if app.config.get('TESTING') else os.getenv('DB_NAME')}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Load the trained model
with open('contact_model.pkl', 'rb') as f:
    CONTACT_MODEL = pickle.load(f)


class Individual(db.Model):
    __tablename__ = 'individuals'
    id = db.Column(db.Integer, primary_key=True)
    unique_id = db.Column(db.String(50), unique=True, nullable=False)
    phone_number = db.Column(db.String(20))


class Contact(db.Model):
    __tablename__ = 'contacts'
    id = db.Column(db.Integer, primary_key=True)
    individual_id = db.Column(db.Integer, db.ForeignKey('individuals.id'))
    contact_id = db.Column(db.Integer, db.ForeignKey('individuals.id'))
    contact_date = db.Column(db.Date, nullable=False)


@app.route('/add_person', methods=['POST'])
def add_person():
    data = request.json
    if not data or 'unique_id' not in data:
        return jsonify({'error': 'Please provide a unique ID'}), 400
    unique_id = data['unique_id']
    phone_number = data.get('phone_number', '')
    if not re.match(r'^(?=.*[a-zA-Z])[a-zA-Z0-9]+$', unique_id):
        return jsonify({'error': 'Unique ID must contain at least one letter and no spaces/special characters'}), 400
    if phone_number and not re.match(r'^\d{7,}$', phone_number):
        return jsonify({'error': 'Phone number must be at least 7 digits (numbers only)'}), 400
    person = Individual(unique_id=unique_id, phone_number=phone_number)
    db.session.add(person)
    try:
        db.session.commit()
        return jsonify({'id': person.id}), 201
    except Exception as e:
        db.session.rollback()
        if 'unique constraint' in str(e).lower():
            return jsonify({'error': f"Sorry, '{unique_id}' is already taken"}), 409
        return jsonify({'error': f"Oops, something went wrong on our end: {str(e)}"}), 500


@app.route('/add_contact', methods=['POST'])
def add_contact():
    data = request.json
    if not all(k in data for k in ['individual_id', 'contact_id', 'contact_date']):
        return jsonify({'error': 'Please fill in all contact details'}), 400
    if data['individual_id'] == data['contact_id']:
        return jsonify({'error': 'A person can’t be their own contact'}), 400
    person1 = db.session.get(Individual, data['individual_id'])
    person2 = db.session.get(Individual, data['contact_id'])
    if not person1:
        return jsonify({'error': f"No person found with ID {data['individual_id']}"}), 404
    if not person2:
        return jsonify({'error': f"No person found with ID {data['contact_id']}"}), 404
    contact = Contact(individual_id=data['individual_id'], contact_id=data['contact_id'],
                      contact_date=data['contact_date'])
    db.session.add(contact)
    try:
        db.session.commit()
        return jsonify({'id': contact.id}), 201
    except Exception as e:
        db.session.rollback()
        if 'unique_contact_per_day' in str(e):
            return jsonify({'error': 'This contact is already logged for today'}), 409
        return jsonify({'error': f"Oops, something went wrong on our end: {str(e)}"}), 500

@app.route('/person/<unique_id>', methods=['GET'])
def get_person(unique_id):
    person = Individual.query.filter_by(unique_id=unique_id).first()
    if not person:
        return jsonify({'error': 'No person found with that ID'}), 404
    return jsonify({'id': person.id, 'unique_id': person.unique_id, 'phone_number': person.phone_number}), 200

@app.route('/contacts/<unique_id>', methods=['GET'])
def get_contacts(unique_id):
    person = Individual.query.filter_by(unique_id=unique_id).first()
    if not person:
        return jsonify({'error': 'No person found with that ID'}), 404

    G = nx.Graph()
    all_contacts = Contact.query.all()
    individuals = {i.id: i.unique_id for i in Individual.query.all()}
    for c in all_contacts:
        G.add_edge(individuals[c.individual_id], individuals[c.contact_id], date=str(c.contact_date))

    direct_outgoing = Contact.query.filter_by(individual_id=person.id).all()
    direct_incoming = Contact.query.filter_by(contact_id=person.id).all()
    direct_contacts = direct_outgoing + direct_incoming
    direct = [{'contact_id': c.contact_id, 'date': str(c.contact_date)} if c.individual_id == person.id
              else {'contact_id': c.individual_id, 'date': str(c.contact_date)}
              for c in direct_contacts]

    predicted = {}
    explanations = {}
    if person.unique_id in G:
        today = datetime.now().date()
        direct_uids = [individuals[c.contact_id] if c.individual_id == person.id else individuals[c.individual_id]
                       for c in direct_contacts]
        for neighbor in G.neighbors(person.unique_id):
            for second_neighbor in G.neighbors(neighbor):
                if second_neighbor != person.unique_id and second_neighbor not in direct_uids:
                    # Features for AI: [neighbor_contacts, days_ago, mutual_contacts]
                    neighbor_contacts = len(list(G.neighbors(neighbor)))
                    contact_dates = [c.contact_date for c in all_contacts if
                                     individuals[c.individual_id] == neighbor or individuals[c.contact_id] == neighbor]
                    days_ago = min([(today - d).days for d in contact_dates], default=30)
                    mutual_contacts = len(set(G.neighbors(person.unique_id)) & set(G.neighbors(second_neighbor)))
                    features = np.array([[neighbor_contacts, days_ago, mutual_contacts]])
                    confidence = CONTACT_MODEL.predict_proba(features)[0][1]
                    explanation = (
                        f"Predicted {second_neighbor} via {neighbor}: "
                        f"Contacts={neighbor_contacts} (high activity boosts chance), "
                        f"Days ago={days_ago} (recent is better), "
                        f"Mutuals={mutual_contacts} (shared ties help),  "
                        f"Confidence={confidence:.2f}"
                    )
                    print(explanation)
                    predicted[second_neighbor] = round(confidence, 2)
                    explanations[second_neighbor] = explanation

    nodes = [{'id': i.id, 'unique_id': i.unique_id,
              'contacts': len(list(G.neighbors(i.unique_id))) if i.unique_id in G else 0}
             for i in Individual.query.all()]
    edges = [{'source': individuals[c.individual_id], 'target': individuals[c.contact_id], 'date': str(c.contact_date)}
             for c in all_contacts]

    return jsonify({
        'direct': direct,
        'predicted': [{'unique_id': uid, 'confidence': conf} for uid, conf in predicted.items()],
        'explanations': explanations,
        'graph': {'nodes': nodes, 'edges': edges}
    })


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
