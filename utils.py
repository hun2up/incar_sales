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

# -------------------------------------------    스트림릿 워터마크 제거    ---------------------------------------------------
def hide_st_style():
    hide_st_style = """
                    <style>
                    #MainMenu {visibility: hidden;}
                    footer {visibility: hidden;}
                    header {visibility: hidden;}
                    </style>
                    """
    st.markdown(hide_st_style, unsafe_allow_html=True)

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

# ----------------------------------------------    데이터 불러오기    -------------------------------------------------------
@st.cache_data(ttl=600)
def call_data(v_month):
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

# ----------------------------------------------    사이드바 제작    -------------------------------------------------------
def make_sidebar(dfv_sidebar, colv_sidebar):
    return st.sidebar.multiselect(
        colv_sidebar,
        options=dfv_sidebar[colv_sidebar].unique(),
        default=dfv_sidebar[colv_sidebar].unique()
    )

##########################################################################################################################
##################################################     차트 (현황)     ####################################################
##########################################################################################################################
# 이거 너무 복잡함 (절차지향적임)
# --------------------------------    그래프 제작을 위한 필요 컬럼 분류하고 누적값 구하기    -----------------------------------
def make_chartdata(dfv_month, category):
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

# 이거 너무 복잡함 (절차지향적임)
# ------------------------------------------------    손생 합계    -------------------------------------------------------
def sum_lnf(dfv_month, dfv_insurance):
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

# 이거 너무 복잡함 (절차지향적임)
# -----------------------------------------------    꺾은선 그래프    ------------------------------------------------------
def make_chart_line(df_linechart, title):
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

##########################################################################################################################
##############################################     스타일 카드 (랭킹)     #################################################
##########################################################################################################################
# ------------------------------------    스타일카드 제작을 위한 필요 컬럼 분류    ------------------------------------------
def make_rankdata(dfv_month, category):
    dfv_category = dfv_month.groupby(category)['영수/환급보험료'].sum().reset_index(name='매출액')
    # 필요컬럼, 영수일자, 영수/환급보험료로 묶고, 영수/환급보험료 합계 구한 뒤 컬럼명을 '매출액'으로 변경
    dfv_category = dfv_category.sort_values(by='매출액', ascending=False)
    dfv_category['매출액'] = dfv_category['매출액'].map('{:,.0f}'.format)
    return dfv_category

# -------------------------------------------    스타일카드(랭킹) 제작    -----------------------------------------------------
def make_cards(dfv_visual, form):
    value = st.columns(5)
    if form == 'single':
        for i in range(5):
            value[i].metric(dfv_visual.iat[i,0], dfv_visual.iat[i,1] + '원')
    elif form == 'multiple':
        for i in range(5):
            value[i].metric(dfv_visual.iat[i,0] + ' (' + dfv_visual.iat[i,1] + ')', dfv_visual.iat[i, 2] + '원')

# -------------------------------------------------    토글 제작    -----------------------------------------------------------
def make_toggles(lst, form):
    for i in range(len(lst[0])):
        st.write(lst[0][i])
        make_cards(lst[1][i], form)

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
def make_subtoggle(count, theme, reference, title):
    # st.columns()에서 뒤쪽부터 토글을 생성 (i를 역순으로 반환하는 for문 정의)
    for i in range(3, 3-count, -1):
        # 3의 역순으로 하위랭크 생성
        if theme[i].toggle(title[3-i]):
            # 타이틀
            st.markdown(f"##### {title[3-i]}")
            # 토글 생성
            make_toggles(reference[3-i], 'multiple')

##########################################################################################################################
##############################################     랭킹 데이터 전처리     #################################################
##########################################################################################################################
class Rank:
    def __init__(self, df):
        self.df = df

    # ------------------------------    스타일카드 제작을 위한 필요 컬럼 분류    ------------------------------
    def make_rankdata_class(self, columns):
        # 입력 받은 컬럼과 '영수/환급보험료' 칼럼으로 묶고 '영수/환급보혐료' 칼럼은 '매출액' 칼럼으로 변경
        df_result = self.df.groupby(columns)['영수/환급보험료'].sum().reset_index(name='매출액')
        # '매출액' 칼럼을 내림차순으로 정렬
        df_result = df_result.sort_values(by='매출액', ascending=False)
        # '매출액' 칼럼을 숫자 형태로 변환
        df_result['매출액'] = df_result['매출액'].map('{:,.0f}'.format)
        return df_result
    
    '''
    # ------------------------------------    보험회사별 하위랭킹 제작    ------------------------------------------
    def make_subrank_company(self, columns, drop):
        df_result = self.make_rankdata_class(columns)
        # 하위랭킹 제작을 위한 5개의 스타일카드 제목 생성
        title = [self.df.iat[i,0] for i in range(5)]
        # 하위랭킹 제작을 위한 5개의 스타일카드 내용 생성
        element = [df_result[df_result['보험회사'].isin([self.df.iat[i,0]])].drop(columns=drop) for i in range(5)]
        return [title, element]
    '''

    # ------------------------------------    상품군별별 하위랭킹 제작    ------------------------------------------
    def make_subrank_category(self, columns, title):
        df_result = self.make_rankdata_class(columns)
        index = [['보장성','기타(보장성)'],['종신/CI'],['CEO정기보험'],['어린이'],['어린이(태아)'],['운전자'],['단독실손'],['연금','연금저축'],['변액연금']]
        # 하위랭킹 제작을 위한 5개의 스타일카드 제목 생성
        title = [f"{index[i]} 매출액 상위 {title}" for i in range(len(index))]
        # 하위랭킹 제작을 위한 5개의 스타일카드 내용 생성
        element = [df_result[df_result['상품군'].isin([index[i]])].drop(columns='상품군') for i in range(len(index))]
        return [title, element]

##########################################################################################################################
######################################     스타일 카드 제작 (Rank 클래스 상속)     #########################################
##########################################################################################################################
class MakeCard(Rank):
    def __init__(self, df):
        super().__init__(df)

    # ----------------------------    라벨이 단일항목으로 구성된 스타일 카드 제작    ----------------------------
    def make_card_single(self, df, number):
        value = st.columns(number) # 카드 노출을 위한 'number'개의 컬럼 제작
        for i in range(number): # 'number'개 만큼 카드 제작하여 노출
            try: value[i].metric(df.iat[i,0], df.iat[i,1] + '원')
            except: pass

    # ---------------------    라벨이 괄호를 포함하는 복수항목으로 구성된 스타일 카드 제작    ---------------------
    def make_card_multiple(self, df, number):
        value = st.columns(number) # 카드 노출을 위한 'number'개의 컬럼 제작
        for i in range(number): # 'number'개 만큼 카드 제작하여 노출
            try: value[i].metric(df.iat[i,0] + '(' + df.iat[i,1] + ')', df.iat[i, 2] + '원')
            except: pass

##########################################################################################################################
##################################     하위랭킹(토글) 제작 (MakeCard 클래스 상속)     ######################################
##########################################################################################################################
class Toggles(MakeCard):
    def __init__(self, df):
        super().__init__(df)

    # ------------------------------------    소속부문별 하위랭킹 제작    ----------------------------------------
    def make_toggles_channel(self, reference, title, form):
        df_channel = self.make_rankdata_class(columns=['소속'])
        df_result = self.make_rankdata_class(reference)
        index = [df_channel.iat[i,0] for i in range(6)]
        # 하위랭킹 제작을 위한 5개의 스타일카드 제목 생성
        for i in range(6):
            st.markdown(f"{index[i]} 매출액 상위 {title}")
            df_subrank = df_result[df_result['소속'].isin([index[i]])].drop(columns='소속')
            if form == 'single':
                self.make_card_single(df=df_subrank, number=5)
            if form == 'multiple':
                self.make_card_multiple(df=df_subrank, number=5)


    # ------------------------------------    보험회사별 하위랭킹 제작    ------------------------------------------
    def make_toggles_company(self, reference, drop, title, form):
        df_company = self.make_rankdata_class(columns=['보험회사'])
        df_result = self.make_rankdata_class(reference)
        for i in range(5):
            st.markdown(f"{df_company.iat[i,0]} 매출액 상위 {title}")
            df_subrank = df_result[df_result['보험회사'].isin([self.df.iat[i,0]])].drop(columns=drop)
            if form =='single':
                self.make_card_single(df=df_subrank, number=5)
            if form == 'multiple':
                self.make_card_multiple(df=df_subrank, number=5)

    # ------------------------------------    보험상품별 하위랭킹 제작    ------------------------------------------
    def make_toggles_product(self, reference, select, drop, form):
        df_result = self.make_rankdata_class(reference)
        df_sub = self.make_rankdata_class(select)
        for i in range(5):
            st.markdown(f"##### {df_result.iat[i,0]} ({df_result.iat[i,1]}")
            df_subrank = df_sub[df_sub['상품명'].isin([df_result.iat[i,0]])].drop(columns=drop)
            if form == 'single':
                self.make_card_single(df=df_subrank, number=5)
            if form== 'multiple':
                self.make_card_multiple(df=df_subrank, number=5)
        