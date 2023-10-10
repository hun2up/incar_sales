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

# -------------------------------------------------    토글 제작    --------------------------------------------------------
def fn_toggle(lst, form):
    for i in range(len(lst[0])):
        st.write(lst[0][i])
        try: fn_ranking(lst[1][i], form) 
        except: pass
        i += 1

def fig_distplot(df, col):
    return pl.figure_factory.create_displot(df, col, bin_size=.2)


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
    ############################################     차트 제작용 전처리     ######################################################
    ##########################################################################################################################
    # -------------------------------------------  매출액 기준 기본 전처리  ----------------------------------------------------
    dfc_insu = fn_visualization(df_month, ['보험종목','영수일자'], 'chart') # 보험종목별 매출액
    dfc_company = fn_visualization(df_month, ['보험회사','영수일자'], 'chart') # 보험회사별 매출액
    dfc_product = fn_visualization(df_month, ['상품군','영수일자'], 'chart') # 상품군별 매출액
    dfc_channel = fn_visualization(df_month, ['소속','영수일자'], 'chart') # 소속부문별 매출액
    df_insu = fn_insurance(df_month, dfc_insu) # 보험종목별(손생) 매출액 데이터에 합계 데이터 삽입: ['보험종목','영수/환급일','매출액']

    ##########################################################################################################################
    ############################################     랭킹 제작용 전처리     ######################################################
    ##########################################################################################################################
    # --------------------------------------------  랭킹 제작 기본 전처리  -------------------------------------------------------
    dfr_chn = fn_visualization(df_month, ['소속'], 'rank') # 소속부문 매출액 순위
    dfr_fa = fn_visualization(df_month, ['담당자코드','담당자','파트너'], 'rank') # FA 매출액 순위
    dfr_fa = dfr_fa.drop(columns='담당자코드')
    dfr_com = fn_visualization(df_month, ['보험회사'], 'rank') # 보험회사 매출액 순이
    dfr_cat = fn_visualization(df_month, ['상품군'], 'rank') # 상품군 매출액 순위
    dfr_prod = fn_visualization(df_month, ['상품명','보험회사'], 'rank') # 보험상품 매출액 순위

    # -------------------------------------------------  부문별 랭킹  -----------------------------------------------------------
    def fn_ranking_channel(dfr, df, title):
        lstv_ranking = [[],[]]
        # 부문 개수(6) 만큼 반복문 실행 (기초 리스트 제작)
        for i in range(6):
            # 기초 리스트에 들어갈 각 랭킹 제목 제작
            lstv_ranking[0].append(f"{dfr.iat[i,0]} 매출액 상위 {title}")
            # 기초 리스트에 들어갈 각 랭킹 스타일카드 제작
            lstv_ranking[1].append(df[df['소속'].isin([dfr.iat[i,0]])].drop(columns=['소속']))
        return lstv_ranking
    
    # 소속부문별 매출액 상위 FA
    dfr_chn_fa = fn_visualization(df_month, ['소속','담당자','파트너'], 'rank')
    lst_chn_fa = fn_ranking_channel(dfr_chn, dfr_chn_fa, "FA")
    
    # 소속부문별 매출액 상위 보험회사
    dfr_chn_com = fn_visualization(df_month, ['소속','보험회사'], 'rank')
    lst_chn_com = fn_ranking_channel(dfr_chn, dfr_chn_com, "보험회사")

    # 소속부문별 매출액 상위 보험상품
    dfr_chn_prod = fn_visualization(df_month, ['소속','상품명','보험회사'], 'rank')
    lst_chn_prod = fn_ranking_channel(dfr_chn, dfr_chn_prod, "보험상품")

    # --------------------------------------------------  FA별 랭킹  -----------------------------------------------------------
    def fn_ranking_fa(dfr, df, value, drop):
        lstv_ranking = [[],[]]
        # 부문 개수(6) 만큼 반복문 실행 (기초 리스트 제작)
        for i in range(5):
            # 기초 리스트에 들어갈 각 랭킹 제목 제작
            lstv_ranking[0].append(dfr.iat[i,1] + ' (' + dfr.iat[i,0] + ')')
            # 기초 리스트에 들어갈 각 랭킹 스타일카드 제작
            lstv_ranking[1].append(df[df[value].isin([dfr.iat[i,0]])].drop(columns=drop))
        return lstv_ranking

    # 매출액 상위 FA별 상위 TOP5 보험상품
    dfr_fa_prod = fn_visualization(df_month, ['담당자','담당자코드','상품명','보험회사'], 'rank')
    lst_fa_prod = fn_ranking_fa(dfr_fa, dfr_fa_prod, '담당자', ['담당자','담당자코드'])

    # -----------------------------------------------  보험회사별 랭킹  -----------------------------------------------------------
    def fn_ranking_com(dfr, df, value, drop):
        lstv_ranking = [[],[]]
        # 부문 개수(6) 만큼 반복문 실행 (기초 리스트 제작)
        for i in range(5):
            # 기초 리스트에 들어갈 각 랭킹 제목 제작
            lstv_ranking[0].append(dfr.iat[i,0])
            # 기초 리스트에 들어갈 각 랭킹 스타일카드 제작
            lstv_ranking[1].append(df[df[value].isin([dfr.iat[i,0]])].drop(columns=drop))
        return lstv_ranking
    
    # 보험회사별 매출액 상위 지점
    dfr_com_ptn = fn_visualization(df_month, ['보험회사','파트너','소속'], 'rank')
    lst_com_ptn = fn_ranking_com(dfr_com, dfr_com_ptn, '보험회사', ['보험회사'])
    # 보험회사별 매출액 상위 FA
    dfr_com_fa = fn_visualization(df_month, ['보험회사','담당자코드','담당자','파트너'], 'rank')
    lst_com_fa = fn_ranking_com(dfr_com, dfr_com_fa, '보험회사', ['보험회사','담당자코드'])
    # 보험회사별 매출액 상위 보험상품
    dfr_com_prod = fn_visualization(df_month, ['보험회사','상품명','상품군'], 'rank')
    lst_com_prod = fn_ranking_com(dfr_com, dfr_com_prod, '보험회사', ['보험회사'])


    # ------------------------------------------------  상품군별 랭킹  -----------------------------------------------------------
    def fn_ranking_category(df, title):
        lst_cat = [['보장성','기타(보장성)'],['종신/CI'],['CEO정기보험'],['어린이'],['어린이(태아)'],['운전자'],['단독실손'],['연금','연금저축'],['변액연금']]
        lstv_ranking = [[],[]]
        for cat_prod in range(len(lst_cat)):
            # 상품군별 매출액 상위 보험상품 제목 제작
            lstv_ranking[0].append(f"상품군별 매출액 상위 {title} ({lst_cat[cat_prod][0]})")
            # 상품군별 매출액 상위 보험상품 스타일카드 제작
            lstv_ranking[1].append(df[df['상품군'].isin(lst_cat[cat_prod])].drop(columns='상품군'))
        return lstv_ranking

    # 상품군별 매출액 상위 지점
    dfr_cat_ptn = fn_visualization(df_month, ['파트너','소속','상품군'], 'rank')
    lst_cat_ptn = fn_ranking_category(dfr_cat_ptn, '지점')
    # 상품군별 매출액 상위 FA
    dfr_cat_fa = fn_visualization(df_month, ['담당자','담당자코드','파트너','상품군'], 'rank')
    dfr_cat_fa = dfr_cat_fa.drop(columns='담당자코드')
    lst_cat_fa = fn_ranking_category(dfr_cat_fa, 'FA')
    # 상품군별 매출액 상위 보험상품
    dfr_cat_prod = fn_visualization(df_month, ['상품명','보험회사','상품군'], 'rank')
    lst_cat_prod = fn_ranking_category(dfr_cat_prod, '보험상품')

    # -----------------------------------------------  보험상품별 랭킹  -----------------------------------------------------------
    def fn_ranking_prod(dfr, df, value, drop):
        lstv_ranking = [[],[]]
        # 부문 개수(6) 만큼 반복문 실행 (기초 리스트 제작)
        for i in range(5):
            # 기초 리스트에 들어갈 각 랭킹 제목 제작
            lstv_ranking[0].append(f"{dfr.iat[i,0]} ({dfr.iat[i,1]})")
            # 기초 리스트에 들어갈 각 랭킹 스타일카드 제작
            lstv_ranking[1].append(df[df[value].isin([dfr.iat[i,0]])].drop(columns=drop))
        return lstv_ranking
    
    # 보험상품별 매출액 상위 지점
    dfr_prod_ptn = fn_visualization(df_month, ['상품명','파트너','소속'], 'rank')
    lst_prod_ptn = fn_ranking_prod(dfr_prod, dfr_prod_ptn, '상품명', ['상품명'])
    # 보험상품별 매출액 상위 FA
    dfr_prod_fa = fn_visualization(df_month, ['상품명','담당자코드','담당자','파트너'], 'rank')
    lst_prod_fa = fn_ranking_prod(dfr_prod, dfr_prod_fa, '상품명', ['상품명','담당자코드'])

    #########################################################################################################################
    ##################################################     차트 제작     #####################################################
    #########################################################################################################################
    # --------------------------------------------  추이 그래프(꺾은선) 제작  -------------------------------------------------
    fig_line_insurnace = fig_linechart(df_insu, '보험종목별 매출액 추이')
    fig_line_company = fig_linechart(dfc_company, '보험회사별 매출액 추이')
    fig_line_product = fig_linechart(dfc_product, '상품군별 매출액 추이')
    fig_line_channel = fig_linechart(dfc_channel, '소속부문별 매출액 추이')
    fig_dist_insurance = fig_distplot(df_insu, ['생명보험','손해보험'])

    ##########################################################################################################################
    ################################################     메인페이지 설정     ##################################################
    ##########################################################################################################################
    # 메인페이지 타이틀
    st.header(f"{this_month} 매출현황 추이 (그래프)")

    # -----------------------------------------------------  차트 노출  ---------------------------------------------------------
    st.plotly_chart(fig_dist_insurance, use_container_width=True)
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
    st.write("랭킹 옵션에  표시된 옵션은 구현완료")

    # 소속부문 매출액 순위는 금액 단위가 커서 '원' 생략
    chn = st.columns([2,1,1,1])
    chn[0].markdown("#### 부문 매출액 순위")
    rchn = st.columns(6)
    for i in range(6):
        rchn[i].metric(dfr_chn.iat[i, 0], dfr_chn.iat[i, 1] + '원')
    # 하위 토글
    if chn[1].toggle("부문별 매출액 상위 FA "):
        st.markdown("##### 부문별 매출액 상위 FA")
        fn_toggle(lst_chn_fa, 'multiple')
    if chn[2].toggle("부문별 매출액 상위 보험회사 "):
        st.markdown("##### 부문별 매출액 상위 보험회사")
        fn_toggle(lst_chn_com, 'single')
    if chn[3].toggle("부문별 매출액 상위 보험상품 "):
        st.markdown("##### 부문별 매출액 상위 보험상품")
        fn_toggle(lst_chn_prod, 'multiple')
    
    st.markdown('---')
    fa = st.columns([2,1,1,1])
    fa[0].markdown("#### 매출액 상위 FA")
    fn_ranking(dfr_fa, 'multiple')
    if fa[3].toggle("매출액 상위 FA 주요 판매상품 "):
        st.markdown("##### 매출액 상위 FA 주요 판매상품")
        fn_toggle(lst_fa_prod, 'multiple')

    st.markdown('---')
    com = st.columns([2,1,1,1])
    com[0].markdown("#### 매출액 상위 보험회사")
    fn_ranking(dfr_com, 'single')
    if com[1].toggle("보험회사별 매출액 상위 지점 "):
        st.markdown("##### 보험회사별 매출액 상위 지점")
        fn_toggle(lst_com_ptn, 'multiple')
    if com[2].toggle("보험회사별 매출액 상위 FA "):
        st.markdown("##### 보험회사별 매출액 상위 FA")
        fn_toggle(lst_com_fa, 'multiple')
    if com[3].toggle("보험회사별 매출액 상위 보험상품 "):
        st.markdown("##### 보험회사별 매출액 상위 보험상품")
        fn_toggle(lst_com_prod, 'multiple')

    st.markdown('---')
    cat = st.columns([2,1,1,1])
    cat[0].markdown("#### 매출액 상위 상품군")
    fn_ranking(dfr_cat, 'single')
    if cat[1].toggle("상품군별 매출액 상위 지점 "):
        st.markdown("##### 상품군별 매출액 상위 부문")
        fn_toggle(lst_cat_ptn, 'multiple')
    if cat[2].toggle("상품군별 매출액 상위 FA "):
        st.markdown("##### 상품군별 매출액 상위 FA")
        fn_toggle(lst_cat_fa, 'multiple')
    if cat[3].toggle("상품군별 매출액 상위 보험상품 "):
        st.markdown("##### 상품군별 매출액 상위 보험상품")
        fn_toggle(lst_cat_prod, 'multiple')

    st.markdown('---')
    prod = st.columns([2,1,1,1])
    prod[0].markdown("#### 매출액 상위 보험상품")
    fn_ranking(dfr_prod, 'multiple')
    if prod[2].toggle("보험상품별 매출액 상위 지점"):
        st.markdown("##### 보험상품별 매출액 상위 지점")
        fn_toggle(lst_prod_ptn, 'multiple')
    if prod[3].toggle("보험상품별 매출액 상위 FA"):
        st.markdown("##### 보험상품별 매출액 상위 FA")
        fn_toggle(lst_prod_fa, 'multiple')