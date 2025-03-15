# PandemicNet MVP

PandemicNet is a contact tracing tool designed for low-tech environments, inspired by real-world pandemic response needs. This Minimum Viable Product (MVP) tracks individuals, logs contacts, and visualizes networks with a graph—all built with Flask, PostgreSQL, and Streamlit.

## Features
- **Add People**: Register users with a unique ID and phone number.
- **Log Contacts**: Record who met whom and when, with validation (no duplicates, no self-contacts).
- **Trace Contacts**: See direct contacts and a network graph for any user.
- **Graph Visualization**: Interactive Plotly graph showing contact networks.
- **Future Plans**: AI-powered contact prediction aiming for 95% accuracy (in progress!).

## Tech Stack
- **Backend**: Flask + SQLAlchemy (PostgreSQL)
- **Frontend**: Streamlit
- **Graphing**: NetworkX + Plotly
- **Environment**: Python 3.12

## Setup
1. **Clone the Repo**:
   ```bash
   git clone https://github.com/DannyMikeGanzaRwabuhama/PandemicNet.git
   cd PandemicNet

2. **Set Up Virtual Environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Database**:
   - Install PostgreSQL and create a database named `pandemicnet`.
   - Create a `.env` file in the root directory with:
     ```
     DB_USERNAME=your_postgres_username
     DB_PASSWORD=your_postgres_password
     DB_HOST=localhost
     DB_NAME=pandemicnet
     ```

5. **Run the App**:
   - Start the Flask API:
     ```bash
     python app.py
     ```
   - In a new terminal, start the Streamlit UI:
     ```bash
     streamlit run ui.py
     ```
   - Open `http://localhost:8501` in your browser.

## Usage
- **Add a Person**: Enter a unique ID (e.g., `user1`) and optional phone number.
- **Add a Contact**: Input two person IDs and a date.
- **Trace Contacts**: Enter a unique ID to see direct contacts and the graph.

## Demo
- Train AI: `python train_model.py`
- Populate DB: `python populate_db.py`
- Open `http://localhost:8501`, trace `user4`—see direct, predicted contacts, and graph.

## Example
- Add `user1`, `user2`, `user3`.
- Log contacts: `user1` → `user2`, `user2` → `user3`.
- Trace `user1`: See `user2` as a direct contact and a graph linking all three.

## Setup
- Add `GOOGLE_API_KEY` to `.env`

**Run**:
```bash
chmod +x start.sh
docker build -t pandemicnet .
docker run -p 5000:5000 -p 8501:8501 pandemicnet
```

## Next Steps
- Integrate a machine learning model for contact prediction (Done).
- Add SMS-based input for low-tech access.
- Support multiple languages (e.g., Kinyarwanda).

## Contributing
Feel free to fork, submit issues, or PRs—let’s make contact tracing better together!
