########################################################################################################################
################################################     라이브러리 호출     ###################################################
########################################################################################################################
import time
import pandas as pd
import plotly as pl
import streamlit as st
import plotly.figure_factory as ff

########################################################################################################################
##############################################     fntion 정의     ####################################################
########################################################################################################################
# ------------------------------    Google Sheet 데이터베이스 호출 및 자료 전처리    ---------------------------------------
month_dict = {'jan':'1월','feb':'2월','mar':'3월','apr':'4월','may':'5월','jun':'6월','jul':'7월','aug':'8월','sep':'9월','oct':'10월','nov':'11월','dec':'12월'}

@st.cache_data(ttl=600)
def fn_call(v_month):
    # 월별 매출현황 불러오기
    dfv_call = pd.read_csv(st.secrets[f"{v_month}_url"].replace("/edit#gid=", "/export?format=csv&gid="))
    # 필요없는 컬럼 삭제
    dfv_call = dfv_call.drop(columns=['SUNAB_PK','납입회차','납입월도','영수유형','확정자','확정일','환산월초','인정실적','실적구분','이관일자','확정유형','계약상태','최초등록일'])
    # 영수/환급보험료 데이터를 숫자로 변환
    dfv_call['영수/환급보험료'] = pd.to_numeric(dfv_call['영수/환급보험료'].str.replace(",",""))
    # 컬럼명 재설정: '영수/환급일' > '영수일자' ('영수/환급보험료' > '매출액' 수정 예정)
    dfv_call.rename(columns={'영수/환급일':'영수일자'}, inplace=True)
    # 불러 온 데이터에서 납입방법 '일시납'인 데이터 삭제
    return dfv_call[~dfv_call['납입방법'].str.contains('일시납')]
    # dfv_call = dfv_call[~dfv_call['납입방법'].str.contains('일시납')]
    # return dfv_call

# ----------------------------------------------    사아드바 제작    -------------------------------------------------------
def fn_sidebar(dfv_sidebar, colv_sidebar):
    return st.sidebar.multiselect(
        colv_sidebar,
        options=dfv_sidebar[colv_sidebar].unique(),
        default=dfv_sidebar[colv_sidebar].unique()
    )

# -------------------------------------------------    화면 구현    -------------------------------------------------------
def fn_peformance(df_month, this_month):
    start_all = time.time()
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
    ##############################################     메인페이지 타이틀     ##################################################
    ##########################################################################################################################
    st.header(f"{this_month} 매출현황 추이 (그래프)")

    ##########################################################################################################################
    ##################################################     차트 (현황)     ####################################################
    ##########################################################################################################################
    start_chart = time.time()
    # --------------------------------    그래프 제작을 위한 필요 컬럼 분류하고 누적값 구하기    -----------------------------------
    def fn_vchart(dfv_month, category):
        # 차트 제작용 (누적 매출액 산출)
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

    # ----------------------------------------------  생손매출액 (꺾은선)  -----------------------------------------------------
    dfc_insu = fn_vchart(df_month, ['보험종목','영수일자']) # 보험종목별 매출액
    df_insu = fn_insurance(df_month, dfc_insu) # 보험종목별(손생) 매출액 데이터에 합계 데이터 삽입: ['보험종목','영수/환급일','매출액']
    st.plotly_chart(fig_linechart(df_insu, '보험종목별 매출액 추이'), use_container_width=True)

    '''
    # ---------------------------------------------  생손매출액 (히스토그램)  --------------------------------------------------
    df_test = df_month.groupby(['보험종목','영수/환급보험료','증권번호'])['증권번호'].count().reset_index(name='구분')
    df_life = df_test[df_test['보험종목'].isin(['생명보험'])]
    df_life = df_life.rename(columns={'영수/환급보험료':'생명보험'})
    df_life = df_life.drop(columns=['보험종목','증권번호','구분'])
    df_fire = df_test[df_test['보험종목'].isin(['손해보험'])]
    df_fire = df_fire.rename(columns={'영수/환급보험료':'손해보험'})
    df_fire = df_fire.drop(columns=['보험종목','증권번호','구분'])
    
    data = [df_life['생명보험'].tolist(), df_fire['손해보험'].tolist()]
    st.dataframe(data)
    labels = ['생명보험','손해보험']
    fig_displot = ff.create_distplot(data, labels, bin_size=.2)
    st.plotly_chart(fig_displot, use_container_width=True)
    '''

    # -----------------------------------------  보험사별 매출액, 상품군별 매출액  ----------------------------------------------
    fig_line_company, fig_line_prod = st.columns(2)
    dfc_company = fn_vchart(df_month, ['보험회사','영수일자']) # 보험회사별 매출액
    fig_line_company.plotly_chart(fig_linechart(dfc_company, '보험회사별 매출액 추이'), use_container_width=True)
    dfc_prod = fn_vchart(df_month, ['상품군','영수일자']) # 상품군별 매출액
    fig_line_prod.plotly_chart(fig_linechart(dfc_prod, '상품군별 매출액 추이'), use_container_width=True)

    # ---------------------------------------  소속부문별 매출액, 입사연차별 매출액  ---------------------------------------------
    fig_line_chn, r2_c2 = st.columns(2)
    dfc_chn = fn_vchart(df_month, ['소속','영수일자']) # 소속부문별 매출액
    fig_line_chn.plotly_chart(fig_linechart(dfc_chn, '소속부문별 매출액 추이'), use_container_width=True)

    end_chart = time.time()
    st.write(f"시간측정(차트) : {end_chart - start_chart} sec")

    ##########################################################################################################################
    ##############################################     스타일 카드 (랭킹)     #################################################
    ##########################################################################################################################
    st.markdown('---')
    st.markdown("## 주요 매출액 순위")

    start_rank = time.time()
    # ------------------------------------    랭킹 디스플레이를 위한 스타일 카드 정의    --------------------------------------------
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

    # ------------------------------------    스타일카드 제작을 위한 필요 컬럼 분류    ------------------------------------------
    def fn_vrank(dfv_month, category):
        dfv_category = dfv_month.groupby(category)['영수/환급보험료'].sum().reset_index(name='매출액')
        # 필요컬럼, 영수일자, 영수/환급보험료로 묶고, 영수/환급보험료 합계 구한 뒤 컬럼명을 '매출액'으로 변경
        dfv_category = dfv_category.sort_values(by='매출액', ascending=False)
        dfv_category['매출액'] = dfv_category['매출액'].map('{:,.0f}'.format)
        return dfv_category

    # -------------------------------------------    스타일카드(랭킹) 제작    -----------------------------------------------------
    def fn_making_card(dfv_visual, form):
        value = st.columns(5)
        if form == 'single':
            for i in range(5):
                value[i].metric(dfv_visual.iat[i,0], dfv_visual.iat[i,1] + '원')
        elif form == 'multiple':
            for i in range(5):
                value[i].metric(dfv_visual.iat[i,0] + ' (' + dfv_visual.iat[i,1] + ')', dfv_visual.iat[i, 2] + '원')
        # style_metric_cards()

    # -------------------------------------------------    토글 제작    -----------------------------------------------------------
    def fn_toggle(lst, form):
        for i in range(len(lst[0])):
            st.write(lst[0][i])
            fn_making_card(lst[1][i], form)

    # ---------------------------------------    소속부문별 하위랭킹 제작    ----------------------------------------------
    def make_rank_channel(df_all, df_result, title):
        index = [df_all.iat[i,0] for i in range(6)]
        # 하위랭킹 제작을 위한 5개의 스타일카드 제목 생성
        title = [f"{index[i]} 매출액 상위 {title}" for i in range(len(index))]
        # 하위랭킹 제작을 위한 5개의 스타일카드 내용 생성
        element = [df_result[df_result['소속'].isin([index[i]])].drop(columns='소속') for i in range(len(index))]
        return [title, element]
    
    # ---------------------------------------    보험회사별 하위랭킹 제작    ----------------------------------------------
    def make_rank_company(df_all, df_result, drop):
        # 하위랭킹 제작을 위한 5개의 스타일카드 제목 생성
        title = [df_all.iat[i,0] for i in range(5)]
        # 하위랭킹 제작을 위한 5개의 스타일카드 내용 생성
        element = [df_result[df_result['보험회사'].isin([df_all.iat[i,0]])].drop(columns=drop) for i in range(5)]
        return [title, element]

    # ---------------------------------------    상품군별별 하위랭킹 제작    ----------------------------------------------
    def make_rank_category(df_result, title):
        index = [['보장성','기타(보장성)'],['종신/CI'],['CEO정기보험'],['어린이'],['어린이(태아)'],['운전자'],['단독실손'],['연금','연금저축'],['변액연금']]
        # 하위랭킹 제작을 위한 5개의 스타일카드 제목 생성
        title = [f"{index[i]} 매출액 상위 {title}" for i in range(len(index))]
        # 하위랭킹 제작을 위한 5개의 스타일카드 내용 생성
        element = [df_result[df_result['상품군'].isin([index[i]])].drop(columns='상품군') for i in range(len(index))]
        return [title, element]
    
    # ---------------------------------------    보험상품별 하위랭킹 제작    ----------------------------------------------
    def make_rank_product(df_all, df_result, drop):
        # 하위랭킹 제작을 위한 5개의 스타일카드 제목 생성
        title = [f"{df_all.iat[i,0]} ({df_all.iat[i,1]})" for i in range(5)]
        # 하위랭킹 제작을 위한 5개의 스타일카드 내용 생성
        element = [df_result[df_result['상품명'].isin([df_all.iat[i,0]])].drop(columns=drop) for i in range(5)]
        return [title, element]

    # --------------------------------------------    하위토글 노출    ---------------------------------------------------
    def make_subtoggle(count, reference, title):
        # st.columns()에서 뒤쪽부터 토글을 생성 (i를 역순으로 반환하는 for문 정의)
        for i in range(3, 3-count, -1):
            # 3의 역순으로 하위랭크 생성
            if prod[i].toggle(title[3-i]):
                # 타이틀
                st.markdown(f"##### {title[3-i]}")
                # 토글 생성
                fn_toggle(reference[3-i], 'multiple')

    # --------------------------------------------------  부문별 랭킹  -----------------------------------------------------------
    start_rchn = time.time()
    # 메인랭킹 (소속부문 매출액 순위)
    dfr_chn = fn_vrank(df_month, ['소속']) 
    chn = st.columns([2,1,1,1])\
    
    chn[0].markdown("#### 부문 매출액 순위")
    rchn = st.columns(6)
    for i in range(6):
        rchn[i].metric(dfr_chn.iat[i, 0], dfr_chn.iat[i, 1] + '원')
    # 세부랭킹 (토글)
    dfr_chn_fa = fn_vrank(df_month, ['소속','담당자','파트너']) # 소속부문별 매출액 상위 FA
    lst_chn_fa = make_rank_channel(dfr_chn, dfr_chn_fa, "FA")
    dfr_chn_com = fn_vrank(df_month, ['소속','보험회사']) # 소속부문별 매출액 상위 보험회사
    lst_chn_com = make_rank_channel(dfr_chn, dfr_chn_com, "보험회사")
    dfr_chn_prod = fn_vrank(df_month, ['소속','상품명','보험회사']) # 소속부문별 매출액 상위 보험상품
    lst_chn_prod = make_rank_channel(dfr_chn, dfr_chn_prod, "보험상품")
    if chn[1].toggle("부문별 매출액 상위 FA (수정)"):
        st.markdown("##### 부문별 매출액 상위 FA")
        fn_toggle(lst_chn_fa, 'multiple')
    if chn[2].toggle("부문별 매출액 상위 보험회사 (수정)"):
        st.markdown("##### 부문별 매출액 상위 보험회사")
        fn_toggle(lst_chn_com, 'single')
    if chn[3].toggle("부문별 매출액 상위 보험상품 (수정)"):
        st.markdown("##### 부문별 매출액 상위 보험상품")
        fn_toggle(lst_chn_prod, 'multiple')
    end_rchn = time.time()
    st.write(f"시간측정(랭킹-부문) : {end_rchn - start_rchn} sec")

    start_rfa = time.time()
    # --------------------------------------------------  FA별  -----------------------------------------------------------
    # 메인랭킹 (FA 매출액 순위)
    dfr_fa = fn_vrank(df_month, ['담당자코드','담당자','파트너']) 
    dfr_fa = dfr_fa.drop(columns='담당자코드')
    dfr_fa_prod = fn_vrank(df_month, ['담당자','담당자코드','상품명','보험회사'])
    dfr_fa_prod = dfr_fa_prod.drop(columns=['담당자','담당자코드'])
    st.markdown('---')
    fa = st.columns([2,1,1,1])
    fa[0].markdown("#### 매출액 상위 FA")
    fn_making_card(dfr_fa, 'multiple')
    # 세부랭킹 (토글)
    if fa[3].toggle("매출액 상위 FA 주요 판매상품 "):
        st.markdown("##### 매출액 상위 FA 주요 판매상품")
        st.dataframe(dfr_fa_prod)
        for c in range(5):
            st.write(dfr_fa.iat[c,1] + ' (' + dfr_fa.iat[c,0] + ')')
            fa_prod = st.columns(5)
            for i in range(5):
                try: fa_prod[i].metric(dfr_fa_prod.iat[i,0] + ' (' + dfr_fa_prod.iat[i,1] + ')', dfr_fa_prod.iat[i, 2] + '원') 
                except: pass
    end_rfa = time.time()
    st.write(f"시간측정(랭킹-FA) : {end_rfa - start_rfa} sec")

    
    # --------------------------------------------------  보험회사별  -----------------------------------------------------------
    start_rcom = time.time()
    # 메인랭킹 (보험회사 매출액 순위)
    dfr_com = fn_vrank(df_month, ['보험회사']) 
    st.markdown('---') # 구분선
    com = st.columns([2,1,1,1]) # 컬럼 나누기
    com[0].markdown("#### 매출액 상위 보험회사") # 제목
    fn_making_card(dfr_com, 'single') # 메인랭킹 노출
    # 세부랭킹 (토글)
    dfr_com_ptn = fn_vrank(df_month, ['보험회사','파트너','소속']) # 보험회사별 매출액 상위 지점
    lst_com_ptn = make_rank_company(dfr_com, dfr_com_ptn, ['보험회사'])
    dfr_com_fa = fn_vrank(df_month, ['보험회사','담당자코드','담당자','파트너']) # 보험회사별 매출액 상위 FA
    lst_com_fa = make_rank_company(dfr_com, dfr_com_fa, ['보험회사','담당자코드'])
    dfr_com_prod = fn_vrank(df_month, ['보험회사','상품명','상품군']) # 보험회사별 매출액 상위 보험상품
    lst_com_prod = make_rank_company(dfr_com, dfr_com_prod, ['보험회사'])
    if com[1].toggle("보험회사별 매출액 상위 지점 (수정)"): # 보험회사별 매출액 상위 지점
        st.markdown("##### 보험회사별 매출액 상위 지점")
        fn_toggle(lst_com_ptn, 'multiple')
    if com[2].toggle("보험회사별 매출액 상위 FA (수정)"): # 보험회사별 매출액 상위 FA
        st.markdown("##### 보험회사별 매출액 상위 FA")
        fn_toggle(lst_com_fa, 'multiple')
    if com[3].toggle("보험회사별 매출액 상위 보험상품 (수정)"): # 보험회사별 매출액 상위 보험상품
        st.markdown("##### 보험회사별 매출액 상위 보험상품")
        fn_toggle(lst_com_prod, 'multiple')
    end_rcom = time.time()
    st.write(f"시간측정(랭킹-보험회사(수정)) : {end_rcom - start_rcom} sec")

    # --------------------------------------------------  상품군별  -----------------------------------------------------------
    start_rcat = time.time()
    # 메인랭킹 (상품군 매출액 순위)
    dfr_cat = fn_vrank(df_month, ['상품군']) 
    st.markdown('---')
    cat = st.columns([2,1,1,1])
    cat[0].markdown("#### 매출액 상위 상품군")
    fn_making_card(dfr_cat, 'single')
    # 세부랭킹 (토글)
    dfr_cat_ptn = fn_vrank(df_month, ['파트너','소속','상품군']) # 상품군별 매출액 상위 지점
    lst_cat_ptn = make_rank_category(dfr_cat_ptn, '지점')
    dfr_cat_fa = fn_vrank(df_month, ['담당자','담당자코드','파트너','상품군']) # 상품군별 매출액 상위 FA
    dfr_cat_fa = dfr_cat_fa.drop(columns='담당자코드')
    lst_cat_fa = make_rank_category(dfr_cat_fa, 'FA')
    dfr_cat_prod = fn_vrank(df_month, ['상품명','보험회사','상품군']) # 상품군별 매출액 상위 보험상품
    lst_cat_prod = make_rank_category(dfr_cat_prod, '보험상품')
    if cat[1].toggle("상품군별 매출액 상위 지점 (수정)"):
        st.markdown("##### 상품군별 매출액 상위 부문")
        fn_toggle(lst_cat_ptn, 'multiple')
    if cat[2].toggle("상품군별 매출액 상위 FA (수정)"):
        st.markdown("##### 상품군별 매출액 상위 FA")
        fn_toggle(lst_cat_fa, 'multiple')
    if cat[3].toggle("상품군별 매출액 상위 보험상품 (수정)"):
        st.markdown("##### 상품군별 매출액 상위 보험상품")
        fn_toggle(lst_cat_prod, 'multiple')
    end_rcat = time.time()
    st.write(f"시간측정(랭킹-상품군) : {end_rcat - start_rcat} sec")
    
    # --------------------------------------------------  보험상품별  -----------------------------------------------------------      
    start_rprod = time.time()
    # 메인랭킹 (보험상품 매출액 순위)
    dfr_prod = fn_vrank(df_month, ['상품명','보험회사']) 
    st.markdown('---') # 구분선
    prod = st.columns([2,1,1,1]) # 컬럼 나누기
    prod[0].markdown("#### 매출액 상위 보험상품") # 제목
    fn_making_card(dfr_prod, 'multiple') # 메인랭킹 노출
    # 세부랭킹 (토글)
    lst_prod = []
    dfr_prod_ptn = fn_vrank(df_month, ['상품명','파트너','소속']) # 보험상품별 매출액 상위 지점
    lst_prod.append(make_rank_product(dfr_prod, dfr_prod_ptn, ['상품명']))
    dfr_prod_fa = fn_vrank(df_month, ['상품명','담당자코드','담당자','파트너']) # 보험상품별 매출액 상위 FA
    lst_prod.append(make_rank_product(dfr_prod, dfr_prod_fa, ['상품명','담당자코드']))
    make_subtoggle(2, lst_prod, ['보험상품별 매출액 상위 지점', '보험상품별 매출액 상위 FA'])


    '''
    if prod[2].toggle("보험상품별 매출액 상위 지점 (수정)"): # 보험상품별 매출액 상위 지점
        st.markdown("##### 보험상품별 매출액 상위 지점")
        fn_toggle(lst_prod_ptn, 'multiple')
    if prod[3].toggle("보험상품별 매출액 상위 FA (수정)"): # 보험상품별 매출액 상위 FA
        st.markdown("##### 보험상품별 매출액 상위 FA")
        fn_toggle(lst_prod_fa, 'multiple')
    '''
    
    end_rprod = time.time()
    st.write(f"시간측정(랭킹-보험상품(수정)) : {end_rprod - start_rprod} sec")

    end_all = time.time()
    st.write(f"시간측정(전체) : {end_all - start_all} sec")

    style_metric_cards()