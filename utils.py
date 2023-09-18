########################################################################################################################
################################################     라이브러리 호출     ###################################################
########################################################################################################################
import pandas as pd
import streamlit as st
import plotly as pl

########################################################################################################################
##############################################     function 정의     ####################################################
########################################################################################################################
# ---------------------------------------    Google Sheet 데이터베이스 호출    ----------------------------------------------
@st.cache_data(ttl=600)
def load_data(sheets_url):
    csv_url = sheets_url.replace("/edit#gid=", "/export?format=csv&gid=")
    return pd.read_csv(csv_url)

def func_dates(year, month):
    start_date = f'{year}-{month}-01'
    end_date = f'{year}-{month}-{pd.Timestamp(year, month + 1, 1) - pd.DateOffset(days=1).day}'
    date_range = pd.date_range(start=start_date, end=end_date)
    df_dates = pd.DataFrame({'dates': date_range})
    return df_dates

# 함수정의: 자료호출 및 전처리
def func_call(month):
    # 월별 매출현황 불러오고, 필요없는 칼럼 삭제
    df_call = load_data(st.secrets[f"{month}_url"]).drop(columns=['SUNAB_PK','납입회차','납입월도','영수유형','확정자','확정일','환산월초','인정실적','실적구분','이관일자','확정유형','계약상태','최초등록일'])
    # 영수/환급보험료 데이터를 숙자로 변환
    df_call['영수/환급보험료'] = pd.to_numeric(df_call['영수/환급보험료'].str.replace(",",""))
    df_call.rename(columns={'영수/환급일':'영수일자'}, inplace=True)
    return df_call

# 함수정의: 필요 칼럼 분류
def func_category(df_month, category):
    df_category = df_month.groupby([category,'영수일자'])['영수/환급보험료'].sum().reset_index(name='매출액')
    return df_category

# 함수정의: 손생 및 손생합계
def func_insurance(df_month, df_insurance):
    df_sum = df_month.groupby(['영수일자'])['영수/환급보험료'].sum().reset_index(name='매출액')
    df_sum['보험종목'] = '손생합계'
    df_sum = df_sum[['보험종목','영수일자','매출액']]
    df_sum = pd.concat([df_insurance, df_sum], axis=0)
    return df_sum

# 함수정의: 누적매출액 계산
def func_running(df_category):
    df_category.columns.values[0] = '구분'
    df_temp = df_category.groupby(['구분'])['구분'].count().reset_index(name="개수")
    list_running = df_temp['구분'].tolist()
    # 반복문 실행을 위한 구간 선언 
    df_total = pd.DataFrame(columns=['구분','영수일자','매출액'])
    for i in range(len(list_running)):
        # 생명보험이나 손해보험만 남기기
        df_running = df_category[df_category.iloc[:,0] == list_running[i]]
        # 누적매출액 구하기
        for running in range(df_category.shape[0]):
            try:
                df_running.iloc[running+1,2] = df_running.iloc[running+1,2] + df_running.iloc[running,2]
            except:
                pass
        df_total = pd.concat([df_total, df_running], axis=0)
    return df_total

'''
list_linechart[0]: dataframe ()
'구분': 참조 컬럼 (보험종목)
'매출액': x축 (매출액)
'영수일자': y축 (영수일자)
title: 차트 제목
'''
def fig_linechart(df_linechart, title):
    fig_line = pl.graph_objs.Figure()
    # Iterate over unique channels and add a trace for each
    for reference in df_linechart['구분'].unique():
        line_data = df_linechart[df_linechart['구분'] == reference]
        fig_line.add_trace(pl.graph_objs.Scatter(
            x=line_data['영수일자'],
            y=line_data['매출액'],
            mode='lines+markers',
            name=reference,
        ))
    # Update the layout
    fig_line.update_layout(
        title=title,
        xaxis_title='영수일자',
        yaxis_title='매출액',
        legend_title='구분',
        hovermode='x',
        template='plotly_white'  # You can choose different templates if you prefer
    )
    return fig_line

'''
list_vbarchart[0]: dataframe ()
list_vbarchart[3]: 색상 리스트 ()
list_vbarchart[4]: outside 리스트 ()
list_vbarchart[5]: 차트 제목
'''
def fig_vbarchart_double(list_vbarchart):
    # 오늘의 신청현황 막대그래프
    fig_vbar1 = pl.graph_objs.Bar(
        x=list_vbarchart[0]['과정명'],
        y=list_vbarchart[0]['목표인원'],
        name='목표인원',
        text=list_vbarchart[0]['목표인원'],
        marker={'color':'grey'}, # 여기수정
        orientation='v'
    )
    fig_fig_vbar2 = pl.graph_objs.Bar(
        x=list_vbarchart[0]['과정명'],
        y=list_vbarchart[0]['신청인원'],
        name='신청인원',
        text=list_vbarchart[0]['신청인원'],
        marker={'color':list_vbarchart[3]},
        orientation='v'
    )
    data_fig_vbar = [fig_vbar1, fig_fig_vbar2]
    layout_fig_vbar = pl.graph_objs.Layout(title=list_vbarchart[5],xaxis={'categoryorder':'array', 'categoryarray':None})
    return_fig_vbar = pl.graph_objs.Figure(data=data_fig_vbar,layout=layout_fig_vbar)
    return_fig_vbar.update_traces(textposition=list_vbarchart[4])
    return_fig_vbar.update_layout(showlegend=True)
    return return_fig_vbar