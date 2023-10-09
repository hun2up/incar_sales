########################################################################################################################
################################################     라이브러리 호출     ###################################################
########################################################################################################################
import pandas as pd
import plotly as pl
import streamlit as st

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
    # 필요컬럼, 영수일자, 영수/환급보험료로 묶고, 영수/환급보험료 합계 구한 뒤 컬럼명을 '매출액'으로 변경
    dfv_category = dfv_month.groupby(category)['영수/환급보험료'].sum().reset_index(name='매출액')
    if form == 'chart':
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
        dfv_category = dfv_category.sort_values(by='매출액', ascending=False)
        dfv_category['매출액'] = dfv_category['매출액'].map('{:,.0f}'.format)
        return dfv_category

# ------------------------------------------------    손생 합계    -------------------------------------------------------
def fn_insurance(dfv_month, dfv_insurance):
    dfv_sum = dfv_month.groupby(['영수일자'])['영수/환급보험료'].sum().reset_index(name='매출액')
    dfv_sum['구분'] = '손생합계'
    dfv_sum = dfv_sum[['구분','영수일자','매출액']]
    dfv_sum.columns.values[0] = '구분'
    # 구분 고유값만 남기기 (보험종목, 보험회사 등)
    dfv_temp = dfv_sum.groupby(['구분'])['구분'].count().reset_index(name="개수")
    # 영수일자 고유값만 남기기 (매출액 없어도 일자를 최대로 지정하기 위함)
    dfv_dates = dfv_sum.groupby(['영수일자'])['영수일자'].count().reset_index(name="개수")
    # 보험회사 또는 보험종목 개수 만큼 반복문 실행 위해 리스트 제작
    list_running = dfv_temp['구분'].tolist()
    # 반복문 실행을 위한 초기 데이터프레임 제작
    dfv_total = pd.DataFrame(columns=['구분','영수일자','매출액'])
    # 반복문 실행을 위한 구간 선언 
    for i in range(len(list_running)):
        # 생명보험이나 손해보험만 남기기
        dfv_base = dfv_sum[dfv_sum.iloc[:,0] == list_running[i]]
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
    dfv_total = pd.concat([dfv_insurance, dfv_total], axis=0)
    return dfv_total

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

# -----------------------------------------------    랭킹 카드 제작    --------------------------------------------------------
def fn_ranking(dfv_visualization, form):
    value = st.columns(5)
    if form == 'single':
        for i in range(5):
            value[i].metric(dfv_visualization.iat[i,0], dfv_visualization.iat[i,1] + '원')
    elif form == 'multiple':
        for i in range(5):
            value[i].metric(dfv_visualization.iat[i,0] + ' (' + dfv_visualization.iat[i,1] + ')', dfv_visualization.iat[i, 2] + '원')
    style_metric_cards()

def fn_ranking_toggle(df, form, range):
    for i in range(len(df[0])):
        st.write(len(df[0]))
        st.write(df[0][i])
        try: fn_ranking(df[1][i], form) 
        except: pass
        i += 1


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

# -------------------------------------------------    화면 구현    -------------------------------------------------------
def fn_peformance(df_month, this_month):
    ###########################################################################################################################
    ###########################################     stremalit 워터마크 숨기기     ##############################################
    ###########################################################################################################################
    hide_st_style = """
                    <style>
                    #MainMenu {visibility: hidden;}
                    footer {visibility: hidden;}
                    header {visibility: hidden;}
                    </style>
                    """
    st.markdown(hide_st_style, unsafe_allow_html=True)
    
    ##########################################################################################################################
    ################################################     자료 전처리     ######################################################
    ##########################################################################################################################
    # -------------------------------------------  매출액 기준 기본 전처리  ----------------------------------------------------
    dfc_insu = fn_visualization(df_month, ['보험종목','영수일자'], 'chart') # 보험종목별 매출액
    dfc_company = fn_visualization(df_month, ['보험회사','영수일자'], 'chart') # 보험회사별 매출액
    dfc_product = fn_visualization(df_month, ['상품군','영수일자'], 'chart') # 상품군별 매출액
    dfc_channel = fn_visualization(df_month, ['소속','영수일자'], 'chart') # 소속부문별 매출액
    df_insu = fn_insurance(df_month, dfc_insu) # 보험종목별(손생) 매출액 데이터에 합계 데이터 삽입: ['보험종목','영수/환급일','매출액']

    # ----------------------------------------------------  랭킹  -----------------------------------------------------------
    dfr_chn = fn_visualization(df_month, ['소속'], 'rank') # 소속부문 매출액 순위
    dfr_fa = fn_visualization(df_month, ['담당자코드','담당자','파트너'], 'rank') # FA 매출액 순위
    dfr_fa = dfr_fa.drop(columns='담당자코드')
    dfr_com = fn_visualization(df_month, ['보험회사'], 'rank') # 보험회사 매출액 순이
    dfr_cat = fn_visualization(df_month, ['상품군'], 'rank') # 상품군 매출액 순위
    dfr_prod = fn_visualization(df_month, ['상품명','보험회사'], 'rank') # 보험상품 매출액 순위

    # 상품군별 상위 TOP5 보험상품
    dfr_cat_prod = fn_visualization(df_month, ['상품명','보험회사','상품군'], 'rank')
    dfr_cat_cover = dfr_cat_prod[dfr_cat_prod['상품군'].isin(['보장성','기타(보장성)'])].drop(columns='상품군') # 보장성
    dfr_cat_whole = dfr_cat_prod[dfr_cat_prod['상품군'].isin(['종신/CI'])].drop(columns='상품군') # 종신/CI
    dfr_cat_ceo = dfr_cat_prod[dfr_cat_prod['상품군'].isin(['CEO정기보험'])].drop(columns='상품군') # CEO정기보험
    dfr_cat_child = dfr_cat_prod[dfr_cat_prod['상품군'].isin(['어린이'])].drop(columns='상품군') # 어린이
    dfr_cat_fetus = dfr_cat_prod[dfr_cat_prod['상품군'].isin(['어린이(태아)'])].drop(columns='상품군') # 어린이(태아)
    dfr_cat_driver = dfr_cat_prod[dfr_cat_prod['상품군'].isin(['운전자'])].drop(columns='상품군') # 운전자
    dfr_cat_real = dfr_cat_prod[dfr_cat_prod['상품군'].isin(['단독실손'])].drop(columns='상품군') # 단독실손
    dfr_cat_pension = dfr_cat_prod[dfr_cat_prod['상품군'].isin(['연금'])].drop(columns='상품군') # 연금
    dfr_cat_vul = dfr_cat_prod[dfr_cat_prod['상품군'].isin(['변액연금'])].drop(columns='상품군') # 변액연금

    # 매출액 상위 FA별 상위 TOP5 보험상품
    dfr_fa_prod = fn_visualization(df_month, ['상품명','보험회사','담당자코드','담당자'], 'rank')
    lst_fa = []
    lst_fa[0][0] = dfr_fa.iat[0,1] + ' (' + dfr_fa.iat[0,0] + ')' # 매출액 1위 
    lst_fa[0][1] = dfr_fa.iat[1,1] + ' (' + dfr_fa.iat[1,0] + ')' # 매출액 2위
    lst_fa[0][2] = dfr_fa.iat[2,1] + ' (' + dfr_fa.iat[2,0] + ')' # 매출액 3위
    lst_fa[0][3] = dfr_fa.iat[3,1] + ' (' + dfr_fa.iat[3,0] + ')' # 매출액 4위
    lst_fa[0][4] = dfr_fa.iat[4,1] + ' (' + dfr_fa.iat[4,0] + ')' # 매출액 5위
    lst_fa[1][0] = dfr_fa_prod[dfr_fa_prod['담당자'].isin([dfr_fa_prod.iat[0, 3]])].drop(columns=['담당자코드','담당자']) # 매출액 1위
    lst_fa[1][1] = dfr_fa_prod[dfr_fa_prod['담당자'].isin([dfr_fa_prod.iat[1, 3]])].drop(columns=['담당자코드','담당자']) # 매출액 2위
    lst_fa[1][2] = dfr_fa_prod[dfr_fa_prod['담당자'].isin([dfr_fa_prod.iat[2, 3]])].drop(columns=['담당자코드','담당자']) # 매출액 3위
    lst_fa[1][3] = dfr_fa_prod[dfr_fa_prod['담당자'].isin([dfr_fa_prod.iat[3, 3]])].drop(columns=['담당자코드','담당자']) # 매출액 4위
    lst_fa[1][4] = dfr_fa_prod[dfr_fa_prod['담당자'].isin([dfr_fa_prod.iat[4, 3]])].drop(columns=['담당자코드','담당자']) # 매출액 5위
    '''
    dfr_fa1 = dfr_fa_prod[dfr_fa_prod['담당자'].isin([dfr_fa_prod.iat[0, 3]])].drop(columns=['담당자코드','담당자']) # 매출액 1위
    dfr_fa2 = dfr_fa_prod[dfr_fa_prod['담당자'].isin([dfr_fa_prod.iat[1, 3]])].drop(columns=['담당자코드','담당자']) # 매출액 2위
    dfr_fa3 = dfr_fa_prod[dfr_fa_prod['담당자'].isin([dfr_fa_prod.iat[2, 3]])].drop(columns=['담당자코드','담당자']) # 매출액 3위
    dfr_fa4 = dfr_fa_prod[dfr_fa_prod['담당자'].isin([dfr_fa_prod.iat[3, 3]])].drop(columns=['담당자코드','담당자']) # 매출액 4위
    dfr_fa5 = dfr_fa_prod[dfr_fa_prod['담당자'].isin([dfr_fa_prod.iat[4, 3]])].drop(columns=['담당자코드','담당자']) # 매출액 5위
    '''

    #########################################################################################################################
    ##################################################     차트 제작     #####################################################
    #########################################################################################################################
    # --------------------------------------------  추이 그래프(꺾은선) 제작  -------------------------------------------------
    fig_line_insurnace = fig_linechart(df_insu, '보험종목별 매출액 추이')
    fig_line_company = fig_linechart(dfc_company, '보험회사별 매출액 추이')
    fig_line_product = fig_linechart(dfc_product, '상품군별 매출액 추이')
    fig_line_channel = fig_linechart(dfc_channel, '소속부문별 매출액 추이')

    ##########################################################################################################################
    ################################################     메인페이지 설정     ##################################################
    ##########################################################################################################################
    # 메인페이지 타이틀
    st.header(f"{this_month} 매출현황 추이 (그래프)")

    # -----------------------------------------------------  차트 노출  ---------------------------------------------------------
    # 첫번째 행 (생손매출액)
    st.plotly_chart(fig_line_insurnace, use_container_width=True)
    # 두번째 행 (보험사별, 상품군별 매출액)
    r1_c1, r1_c2 = st.columns(2)
    r1_c1.plotly_chart(fig_line_company, use_container_width=True)
    r1_c2.plotly_chart(fig_line_product, use_container_width=True)
    # 세번째 행 (소속부문별, 입사연차별 매출액)
    r2_c1, r2_c2 = st.columns(2)
    r2_c1.plotly_chart(fig_line_channel, use_container_width=True)

    # ----------------------------------------------------  랭킹  -----------------------------------------------------------       
    st.markdown('---')
    st.markdown("## 전체 현황 요약")
    st.write("랭킹 옵션에 (완) 표시된 옵션은 구현완료")

    # 소속부문 매출액 순위는 금액 단위가 커서 '원' 생략
    chn = st.columns([2,1,1,1])
    chn[0].markdown("#### 부문 매출액 순위")
    rchn = st.columns(6)
    for i in range(6):
        rchn[i].metric(dfr_chn.iat[i, 0], dfr_chn.iat[i, 1])
    if chn[1].toggle("부문별 매출액 상위 FA"):
        st.markdown("##### 부문별 매출액 상위 FA")
    if chn[2].toggle("부문별 매출액 상위 보험회사"):
        st.markdown("##### 부문별 매출액 상위 보험회사")
    if chn[3].toggle("부문별 매출액 상위 보험상품"):
        st.markdown("##### 부문별 매출액 상위 보험상품")
    
    st.markdown('---')
    fa = st.columns([2,1,1,1])
    fa[0].markdown("#### 매출액 상위 FA")
    fn_ranking(dfr_fa, 'multiple')
    if fa[3].toggle("매출액 상위 FA 주요 판매상품 (완)"):
        st.markdown("##### 매출액 상위 FA 주요 판매상품")
        fn_ranking_toggle(lst_fa, 'multiple')
        '''
        st.write(dfr_fa.iat[0,1] + ' (' + dfr_fa.iat[0,0] + ')') # 매출액 1위
        try: fn_ranking(dfr_fa1, 'multiple')
        except: pass
        st.write(dfr_fa.iat[1,1] + ' (' + dfr_fa.iat[1,0] + ')') # 매출액 2위
        try: fn_ranking(dfr_fa2, 'multiple') 
        except: pass
        st.write(dfr_fa.iat[2,1] + ' (' + dfr_fa.iat[2,0] + ')') # 매출액 3위
        try: fn_ranking(dfr_fa3, 'multiple')
        except: pass
        st.write(dfr_fa.iat[3,1] + ' (' + dfr_fa.iat[3,0] + ')') # 매출액 4위
        try: fn_ranking(dfr_fa4, 'multiple')
        except: pass
        st.write(dfr_fa.iat[4,1] + ' (' + dfr_fa.iat[4,0] + ')') # 매출액 5위
        try: fn_ranking(dfr_fa5, 'multiple')
        except: pass
        '''
        

    st.markdown('---')
    com = st.columns([2,1,1,1])
    com[0].markdown("#### 매출액 상위 TOP5 (보험회사)")
    fn_ranking(dfr_com, 'single')
    if com[1].toggle("보험회사별 매출액 상위 부문"):
        st.markdown("##### 보험회사별 매출액 상위 부문")
    if com[2].toggle("보험회사별 매출액 상위 FA"):
        st.markdown("##### 보험회사멸 매출액 상위 FA")
    if com[3].toggle("보험회사별 매출액 상위 보험상품"):
        st.markdown("##### 보험회사별 매출액 상위 보험상품")

    st.markdown('---')
    cat = st.columns([2,1,1,1])
    cat[0].markdown("#### 매출액 상위 TOP5 (상품군)")
    fn_ranking(dfr_cat, 'single')
    if cat[1].toggle("상품군별 매출액 상위 부문"):
        st.markdown("##### 상품군별 매출액 상위 부문")
    if cat[2].toggle("상품군별 매출액 상위 FA"):
        st.markdown("##### 상품군별 매출액 상위 FA")
    if cat[3].toggle("상품군별 매출액 상위 보험상품 (완)"):
        st.markdown("##### 상품군별 매출액 상위 보험상품")
        st.write("상품군별 매출액 상위 TOP5 보험상품 (보장성)")
        try: fn_ranking(dfr_cat_cover, 'multiple')
        except: pass
        st.write("상품군별 매출액 상위 TOP5 보험상품 (종신/CI)")
        try: fn_ranking(dfr_cat_whole, 'multiple')
        except: pass
        st.write("상품군별 매출액 상위 TOP5 보험상품 (CEO정기보험)")
        try: fn_ranking(dfr_cat_ceo, 'multiple')
        except: pass
        st.write("상품군별 매출액 상위 TOP5 보험상품 (어린이)")
        try: fn_ranking(dfr_cat_child, 'multiple')
        except: pass
        st.write("상품군별 매출액 상위 TOP5 보험상품 (어린이(태아))")
        try: fn_ranking(dfr_cat_fetus, 'multiple')
        except: pass
        st.write("상품군별 매출액 상위 TOP5 보험상품 (운전자)")
        try: fn_ranking(dfr_cat_driver, 'multiple')
        except: pass
        st.write("상품군별 매출액 상위 TOP5 보험상품 (단독실손)")
        try: fn_ranking(dfr_cat_real, 'multiple')
        except: pass
        st.write("상품군별 매출액 상위 TOP5 보험상품 (연금)")
        try: fn_ranking(dfr_cat_pension, 'multiple')
        except: pass
        st.write("상품군별 매출액 상위 TOP5 보험상품 (변액연금)")
        try: fn_ranking(dfr_cat_vul, 'multiple')
        except: pass

    st.markdown('---')
    prod = st.columns([2,1,1,1])
    prod[0].markdown("#### 매출액 상위 TOP5 (보험상품)")
    fn_ranking(dfr_prod, 'multiple')
    if prod[2].toggle("보험상품별 매출액 상위 부문"):
        st.markdwon("##### 보험상품별 매출액 상위 부문")
    if prod[3].toggle("보험상품별 매출액 상위 FA"):
        st.markdown("##### 보험상품별 매출액 상위 FA")