import streamlit as st
import random
import requests
import datetime
import plotly.graph_objects as go
import networkx as nx
from dotenv import load_dotenv
import os
import google.generativeai as genai
import threading
import queue

load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
model = genai.GenerativeModel('gemini-2.0-flash')


def generate_explanation(unique_id, confidence, contacts, days, mutuals, result_container):
    try:
        prompt = (
            f"Craft a fun, short explanation for meeting {unique_id} with {confidence:.2f} confidence, "
            f"{contacts} contacts, {days} days ago, {mutuals} mutual connections."
        )
        response = model.generate_content(prompt)
        result_queue.put((unique_id, response.text.strip()))
    except Exception:
        # Fallback to mock if Gemini fails
        vibe = "hot" if confidence >= 0.7 else "maybe" if confidence >= 0.5 else "wild guess"
        days_str = f"{days} day{'s' if days != 1 else ''} ago"
        mutual_str = f"{mutuals} shared connection{'s' if mutuals != 1 else ''}"
        text = random.choice([
            f"{vibe.capitalize()} tip: {unique_id} might’ve crossed paths! {
                contacts} moves, {days_str}. Odds: {confidence:.2f}.",
            f"Check it: {contacts} hits in {days_str} tie {unique_id} to you. {
                mutual_str}—{vibe} shot at {confidence:.2f}!",
            f"{vibe.upper()} ALERT: {unique_id}’s {contacts} links {days_str}, {
                mutual_str}. Confidence: {confidence:.2f}!"
        ])

        if isinstance(result_container, dict):
            result_container[unique_id] = text
        elif isinstance(result_container, queue.Queue):
            result_container.put((unique_id, text))
        else:
            raise ValueError("result_container must be dict or Queue")


st.title("PandemicNet MVP Demo")

# Add a person
st.header("Add Person")
unique_id = st.text_input("Unique ID (e.g., 'user1', not just numbers)")
phone = st.text_input("Phone Number (7+ digits, optional)", value="")
if st.button("Add Person"):
    response = requests.post("http://localhost:5000/add_person", json={"unique_id": unique_id, "phone_number": phone})
    if response.status_code == 201:
        st.success(f"Person added! ID: {response.json()['id']}")
    else:
        try:
            error_msg = response.json().get('error', 'Unknown error from server')
        except ValueError:
            error_msg = f"Server returned invalid response: {response.text}"
        st.error(f"Oops: {error_msg}")

# Add a contact
st.header("Add Contact")
person_id = st.number_input("Person ID", min_value=1, step=1)
contact_id = st.number_input("Contact ID", min_value=1, step=1)
date = st.date_input("Contact Date", value=datetime.date.today())
if st.button("Add Contact"):
    response = requests.post("http://localhost:5000/add_contact",
                             json={"individual_id": person_id, "contact_id": contact_id, "contact_date": str(date)})
    if response.status_code == 201:
        st.success(f"Contact added! ID: {response.json()['id']}")
    else:
        try:
            error_msg = response.json().get('error', 'Unknown error from server')
        except ValueError:
            error_msg = f"Server returned invalid response: {response.text}"
        st.error(f"Oops: {error_msg}")

# Trace contacts with graph
st.header("Trace Contacts")
trace_id = st.text_input("Trace Contacts for Unique ID")
if st.button("Trace"):
    response = requests.get(f"http://localhost:5000/contacts/{trace_id}")
    if response.status_code == 200:
        data = response.json()

        # Direct contacts
        if data['direct']:
            st.write("Direct contacts:", data['direct'])
        else:
            st.info("No direct contacts found.")

        # Graph
        try:
            graph = data['graph']
            G = nx.Graph()
            for node in graph['nodes']:
                G.add_node(node['unique_id'])
            for edge in graph['edges']:
                G.add_edge(edge['source'], edge['target'], date=edge['date'])
            pos = nx.spring_layout(G, k=0.5, iterations=50)

            edge_x = []
            edge_y = []
            edge_hover = []
            for edge in graph['edges']:
                x0, y0 = pos[edge['source']]
                x1, y1 = pos[edge['target']]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
                edge_hover.append(f"{edge['source']} → {edge['target']} on {edge['date']}")

            edge_trace = go.Scatter(
                x=edge_x, y=edge_y,
                line=dict(width=1, color='gray'),
                hoverinfo='text',
                text=edge_hover[::3],
                mode='lines'
            )

            node_x = [pos[node['unique_id']][0] for node in graph['nodes']]
            node_y = [pos[node['unique_id']][1] for node in graph['nodes']]
            node_text = [f"{node['unique_id']}" for node in graph['nodes']]
            node_hover = [f"ID: {node['id']}<br>Contacts: {node['contacts']}" for node in graph['nodes']]
            node_colors = []
            direct_ids = [c['contact_id'] for c in data['direct']]
            predicted_ids = [next(n['id'] for n in graph['nodes'] if n['unique_id'] == p['unique_id']) for p in
                             data['predicted']]
            for node in graph['nodes']:
                if node['unique_id'] == trace_id:
                    node_colors.append('green')
                elif node['id'] in direct_ids:
                    node_colors.append('blue')
                elif node['id'] in predicted_ids:
                    node_colors.append('orange')
                else:
                    node_colors.append('LightSkyBlue')

            node_trace = go.Scatter(
                x=node_x, y=node_y,
                mode='markers+text',
                text=node_text,
                textposition='top center',
                hoverinfo='text',
                hovertext=node_hover,
                marker=dict(size=15, color=node_colors, line=dict(width=2, color='DarkSlateGrey'))
            )

            fig = go.Figure(data=[edge_trace, node_trace],
                            layout=go.Layout(
                                title=f"Contact Network for {trace_id}",
                                showlegend=False,
                                hovermode='closest',
                                margin=dict(b=20, l=5, r=5, t=40),
                                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                width=600,
                                height=600
            ))
            st.plotly_chart(fig)

            # Color legend in expander
            with st.expander("Show Color Legend"):
                st.markdown("""
                - <span style='color: green'>●</span> Traced person ({})
                - <span style='color: blue'>●</span> Direct contacts
                - <span style='color: orange'>●</span> Predicted contacts (AI)
                - <span style='color: LightSkyBlue'>●</span> Other individuals
                """.format(trace_id), unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Oops, couldn’t draw the graph: {str(e)}")

        # Predicted contacts with spinner
        if data['predicted']:
            st.subheader("Predicted Contacts")
            explanations = {}
            threads = []

            # Predicted contacts
            if data['predicted']:
                st.subheader("Predicted Contacts")
                result_queue = queue.Queue()
                threads = []

                with st.spinner("🔄 Crunching AI predictions..."):
                    for pred in data['predicted']:
                        confidence = pred['confidence']
                        explanation = data['explanations'][pred['unique_id']].split(": ", 1)[1]
                        parts = [part.split(' (')[0] for part in explanation.split(', ')]
                        if len(parts) != 4:
                            st.error(f"Explanation parse error: {parts}")
                            continue
                        contacts, days, mutuals, conf = parts
                        contacts, days, mutuals = int(contacts.split('=')[1]), int(days.split('=')[1]), int(
                            mutuals.split('=')[1])

                        thread = threading.Thread(
                            target=generate_explanation,
                            args=(pred['unique_id'], confidence, contacts, days, mutuals, result_queue)
                        )
                        threads.append(thread)
                        thread.start()

                    # Timeout after 10 seconds
                    for thread in threads:
                        thread.join(timeout=10)
                    explanations = dict(result_queue.queue)  # Get what’s done

                for pred in data['predicted']:
                    confidence = pred['confidence']
                    color = "green" if confidence >= 0.7 else "orange" if confidence >= 0.5 else "red"
                    with st.expander(f"{pred['unique_id']} (Confidence: {confidence})"):
                        dynamic_text = explanations.get(pred['unique_id'], "AI timed out—using fallback!")
                        st.markdown(f":{color}[●] {dynamic_text}")

            if not data['direct'] and not data['predicted']:
                st.info("No contacts found for this person.")

    else:
        try:
            error_msg = response.json().get('error', 'Unknown error from server')
        except ValueError:
            error_msg = f"Server returned invalid response: {response.text}"
        st.error(f"Oops: {error_msg}")
