########################################################################################################################
################################################     라이브러리 호출     ###################################################
########################################################################################################################
import pandas as pd
import streamlit as st
import plotly as pl
from datetime import datetime

########################################################################################################################
##############################################     function 정의     ####################################################
########################################################################################################################
# ---------------------------------------    Google Sheet 데이터베이스 호출    ----------------------------------------------
@st.cache_data(ttl=600)
def load_data(sheets_url):
    csv_url = sheets_url.replace("/edit#gid=", "/export?format=csv&gid=")
    return pd.read_csv(csv_url)

'''
list_linechart[0]: dataframe (df_stat, df_trnd)
list_linechart[1]: 참조 컬럼 (소속부문, 입사연차, 과정명)
list_linechart[2]: 데이터 (신청인원, 신청누계, 수료인원, 수료누계, 수료율, IMO신청률 등)
list_linechart[3]: 차트 제목
list_linechart[4]: df_apply: '월' / df_attend: '날짜'
'''
def fig_linechart(list_linechart):
    fig_line = pl.graph_objs.Figure()
    # Iterate over unique channels and add a trace for each
    for reference in list_linechart[0][list_linechart[1]].unique():
        line_data = list_linechart[0][list_linechart[0][list_linechart[1]] == reference]
        fig_line.add_trace(pl.graph_objs.Scatter(
            x=line_data[list_linechart[3]],
            y=line_data[list_linechart[2]],
            mode='lines+markers',
            name=reference,
        ))
    # Update the layout
    fig_line.update_layout(
        title=list_linechart[4],
        xaxis_title=list_linechart[3],
        yaxis_title=list_linechart[2],
        legend_title=list_linechart[1],
        hovermode='x',
        template='plotly_white'  # You can choose different templates if you prefer
    )
    return fig_line