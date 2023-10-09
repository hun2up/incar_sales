########################################################################################################################
################################################     라이브러리 호출     ###################################################
########################################################################################################################
import pandas as pd
import streamlit as st
import plotly as pl

########################################################################################################################
##############################################     fntion 정의     ####################################################
########################################################################################################################
# ---------------------------------------    Google Sheet 데이터베이스 호출    ----------------------------------------------
month_dict = {'jan':'1월','feb':'2월','mar':'3월','apr':'4월','may':'5월','jun':'6월','jul':'7월','aug':'8월','sep':'9월','oct':'10월','nov':'11월','dec':'12월'}

@st.cache_data(ttl=600)
def load_data(sheets_url):
    csv_url = sheets_url.replace("/edit#gid=", "/export?format=csv&gid=")
    return pd.read_csv(csv_url)

# ----------------------------------------------    사아드바 제작    -------------------------------------------------------
def fn_sidebar(dfv_sidebar, colv_sidebar):
    return st.sidebar.multiselect(
        colv_sidebar,
        options=dfv_sidebar[colv_sidebar].unique(),
        default=dfv_sidebar[colv_sidebar].unique()
    )

# -----------------------------------------------    자료 전처리    -------------------------------------------------------
def fn_call(v_month):
    # 월별 매출현황 불러오고, 필요없는 칼럼 삭제
    dfv_call = load_data(st.secrets[f"{v_month}_url"]).drop(columns=['SUNAB_PK','납입회차','납입월도','영수유형','확정자','확정일','환산월초','인정실적','실적구분','이관일자','확정유형','계약상태','최초등록일'])
    # 영수/환급보험료 데이터를 숫자로 변환
    dfv_call['영수/환급보험료'] = pd.to_numeric(dfv_call['영수/환급보험료'].str.replace(",",""))
    # 컬럼명 재설정: '영수/환급일' > '영수일자' ('영수/환급보험료' > '매출액' 수정 예정)
    dfv_call.rename(columns={'영수/환급일':'영수일자'}, inplace=True)
    # 불러 온 데이터에서 납입방법 '일시납'인 데이터 삭제
    dfv_call = dfv_call[~dfv_call['납입방법'].str.contains('일시납')]
    return dfv_call

# ---------------------------------------    그래프 제작을 위한 필요 컬럼 분류    ----------------------------------------------
def fn_visualization(dfv_month, category, form):
    # 차트 제작용 (누적 매출액 산출)
    if form == 'chart':
        # 필요컬럼, 영수일자, 영수/환급보험료로 묶고, 영수/환급보험료 합계 구한 뒤 컬럼명을 '매출액'으로 변경
        dfv_category = dfv_month.groupby(category)['영수/환급보험료'].sum().reset_index(name='매출액')
        dfv_category.columns.values[0] = '구분'
        # 구분 고유값만 남기기 (보험종목, 보험회사 등)
        dfv_temp = dfv_category.groupby(['구분'])['구분'].count().reset_index(name="개수")
        # 영수일자 고유값만 남기기 (매출액 없어도 일자를 최대로 지정하기 위함)
        dfv_dates = dfv_category.groupby(['영수일자'])['영수일자'].count().reset_index(name="개수")
        # 보험회사 또는 보험종목 개수 만큼 반복문 실행 위해 리스트 제작
        list_running = dfv_temp['구분'].tolist()
        # 반복문 실행을 위한 초기 데이터프레임 제작
        dfv_total = pd.DataFrame(columns=['구분','영수일자','매출액'])
        # 반복문 실행을 위한 구간 선언 
        for i in range(len(list_running)):
            # 생명보험이나 손해보험만 남기기
            dfv_base = dfv_category[dfv_category.iloc[:,0] == list_running[i]]
            dfv_running = dfv_base.merge(dfv_dates, on='영수일자', how='right')
            # 최대한의 날짜프레임에 보험사별 매출현황 끼워넣기
            for insert in range(dfv_running.shape[0]):
                if pd.isna(dfv_running.iloc[insert, 0]):
                    dfv_running.iloc[insert,0] = list_running[i]
                    dfv_running.iloc[insert,2] = 0
                else:
                    pass
            # 누적매출액 구하기
            for running in range(dfv_running.shape[0]):
                try:
                    dfv_running.iloc[running+1,2] = dfv_running.iloc[running+1,2] + dfv_running.iloc[running,2]
                except:
                    pass
            dfv_total = pd.concat([dfv_total, dfv_running], axis=0)
        return dfv_total
    # 랭킹 제작용
    elif form == 'rank':
        # 필요컬럼, 영수일자, 영수/환급보험료로 묶고, 영수/환급보험료 합계 구한 뒤 컬럼명을 '매출액'으로 변경
        dfv_category = dfv_month.groupby(category)['영수/환급보험료'].sum().reset_index(name='매출액')
        dfv_category['매출액'] = dfv_category['매출액'].map('{:,.0f}'.format)
        return dfv_category

# ------------------------------------------------    손생 합계    -------------------------------------------------------
def fn_insurance(dfv_month, dfv_insurance):
    dfv_sum = dfv_month.groupby(['영수일자'])['영수/환급보험료'].sum().reset_index(name='매출액')
    dfv_sum['보험종목'] = '손생합계'
    dfv_sum = dfv_sum[['보험종목','영수일자','매출액']]
    dfv_sum = pd.concat([dfv_insurance, dfv_sum], axis=0)
    return dfv_sum

# ----------------------------------------------    누적 매출액 계산    ----------------------------------------------------
def fn_ranking(dfv_visualization, title, values, counts, form):
    st. write(title)
    values = st.columns(counts)
    if form == 'single':
        for i in range(counts):
            values[i].metric(dfv_visualization.iat[i, 0] + ' (' + dfv_visualization.iat[i,1] + ')', dfv_visualization[i, 2] + '원')
    elif form == 'multiple':
        for i in range(counts):
            values[i].metric(dfv_visualization.iat[i, 0], dfv_visualization[i, 1] + '원')

# -----------------------------------------------    꺾은선 그래프    ------------------------------------------------------
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

# ------------------------------------------------    막대 그래프    ------------------------------------------------------
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

# ---------------------------------------    랭킹 디스플레이를 위한 스타일 카드    ----------------------------------------------
def style_metric_cards(
    border_size_px: int = 1,
    border_color: str = "#CCC",
    border_radius_px: int = 5,
    border_left_color: str = "rgb(55,126,184)",
    box_shadow: bool = True,
):

    box_shadow_str = (
        "box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15) !important;"
        if box_shadow
        else "box-shadow: none !important;"
    )
    st.markdown(
        f"""
        <style>
            div[data-testid="metric-container"] {{
                border: {border_size_px}px solid {border_color};
                padding: 5% 5% 5% 10%;
                border-radius: {border_radius_px}px;
                border-left: 0.5rem solid {border_left_color} !important;
                {box_shadow_str}
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


    