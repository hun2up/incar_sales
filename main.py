# streamlit_app.py
import pandas as pd
import streamlit as st
from google.oauth2 import service_account
from gsheetsdb import connect

# Create a connection object.
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
    ],
)
conn = connect(credentials=credentials)

# Perform SQL query on the Google Sheet.
# Uses st.cache_data to only rerun when the query changes or after 10 min.
@st.cache_data(ttl=600)
def run_query(query):
    rows = conn.execute(query, headers=1)
    rows = rows.fetchall()
    return rows

sheet_url = st.secrets["https://docs.google.com/spreadsheets/d/1O54Xqw6tNLhJGGrlfh6V_Lje0rO_xUc1h0sTfPaJoiw/edit#gid=0l"]
rows = run_query(f'SELECT * FROM "{sheet_url}"')

dataframe = pd.DataFrame(rows)