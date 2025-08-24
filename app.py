# app.py
import streamlit as st
from load_sample_data import init_session_state
from chart_page import render_chart_page

st.set_page_config(page_title="Monthly Customer Revenue (User Interface)", layout="wide")

# --- Initialize session state with cached data ---
init_session_state()

# --- Render the chart page ---
render_chart_page()
