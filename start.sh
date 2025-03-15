#!/bin/bash
echo "Starting PandemicNet..."
python app.py &
streamlit run ui.py --server.port 8501