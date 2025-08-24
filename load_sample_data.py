# load_sample_data.py
import streamlit as st
import pandas as pd
import time

@st.cache_data
def load_sample_data():
    # Step 1: Read Excel
    df = pd.read_excel("customer_raw_data.xlsx")
    time.sleep(0.3)  # simulate delay

    # Step 2: Clean Year / Month
    df['Year'] = df['Year'].astype(int).astype(str)
    df['Month'] = df['Month'].astype(int).astype(str).str.zfill(2)
    time.sleep(0.3)

    # Step 3: Create Period column
    df['Period'] = pd.to_datetime(df['Year'] + "-" + df['Month'], format="%Y-%m")
    time.sleep(0.3)

    return df

def init_session_state():
    """Ensure data is loaded into session_state only once."""
    if "official_data" not in st.session_state:
        df = load_sample_data()
        st.session_state["official_data"] = df
        st.session_state["selected_site"] = df["Site"].unique()[0]  # init site
