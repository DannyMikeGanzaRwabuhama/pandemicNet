import streamlit as st
import requests
import datetime
import plotly.graph_objects as go
import networkx as nx

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
        if data['direct']:
            st.write("Direct contacts:", data['direct'])
        if data['predicted']:
            st.write("Predicted contacts:", data['predicted'])
        if not data['direct'] and not data['predicted']:
            st.info("No contacts found for this person.")

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
    else:
        try:
            error_msg = response.json().get('error', 'Unknown error from server')
        except ValueError:
            error_msg = f"Server returned invalid response: {response.text}"
        st.error(f"Oops: {error_msg}")
