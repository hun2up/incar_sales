########################################################################################################################
################################################     라이브러리 호출     ###################################################
########################################################################################################################
import pandas as pd
import plotly as pl
import streamlit as st
from plotly.subplots import make_subplots
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

@st.cache_data(ttl=600)
def call_data_year(category):
    # 연간실적종합 불러오기
    df_call = pd.read_csv(st.secrets[f"{category}_url"].replace("/edit#gid=", "/export?format=csv&gid="))
    return df_call

# ----------------------------------------------    사이드바 제작    -------------------------------------------------------
def make_sidebar(dfv_sidebar, colv_sidebar):
    return st.sidebar.multiselect(
        colv_sidebar,
        options=dfv_sidebar[colv_sidebar].unique(),
        default=dfv_sidebar[colv_sidebar].unique()
    )

##########################################################################################################################
#############################################     차트 데이터 전처리     ################################################
##########################################################################################################################
class ChartData:
    def __init__(self, df):
        self.df = df
        
    def make_data_running(self, select, dates, category):
        # 반복문 실행을 위한 초기 데이터프레임 제작
        df_total = pd.DataFrame(columns=['구분','영수일자','매출액'])
        df_year = pd.DataFrame(columns=['구분','영수일자','매출액'])
        # self.df_year = pd.DataFrame(columns=['구분','영수일자','매출액'])
        # 반복문 실행을 위한 구간 선언 
        for i in range(len(category)):
            # 생명보험이나 손해보험만 남기기
            df_base = select[select.iloc[:,0] == category[i]]
            df_running = df_base.merge(dates, on='영수일자', how='right')
            # 최대한의 날짜프레임에 보험사별 매출현황 끼워넣기
            for insert in range(df_running.shape[0]):
                if pd.isna(df_running.iloc[insert, 0]):
                    df_running.iloc[insert,0] = category[i]
                    df_running.iloc[insert,2] = 0
                else:
                    pass
            # 누적매출액 구하기
            for running in range(df_running.shape[0]):
                try:
                    df_running.iloc[running+1,2] = df_running.iloc[running+1,2] + df_running.iloc[running,2]
                except:
                    pass
            df_year = pd.concat([df_year, df_running.iloc[[-1]]], axis=0)
            df_total = pd.concat([df_total, df_running], axis=0)
        return df_year, df_total

    # --------------------------------    그래프 제작을 위한 필요 컬럼 분류하고 누적값 구하기    -----------------------------------
    def make_data_basic(self, column_select):
        # 차트 제작용 (누적 매출액 산출)
        # 필요컬럼, 영수일자, 영수/환급보험료로 묶고, 영수/환급보험료 합계 구한 뒤 컬럼명을 '매출액'으로 변경
        df_select = self.df.groupby(column_select)['영수/환급보험료'].sum().reset_index(name='매출액')
        df_select.columns.values[0] = '구분'
        # 구분 고유값만 남기기 (보험종목, 보험회사 등)
        df_present = df_select.groupby(['구분'])['구분'].count().reset_index(name="개수")
        # 영수일자 고유값만 남기기 (매출액 없어도 일자를 최대로 지정하기 위함)
        df_dates = df_select.groupby(['영수일자'])['영수일자'].count().reset_index(name="개수")
        # 보험회사 또는 보험종목 개수 만큼 반복문 실행 위해 리스트 제작
        df_category = df_present['구분'].tolist()
        df_year, df_total = self.make_data_running(select=df_select, dates=df_dates, category=df_category)
        return df_year, df_total
    
    def make_data_sum(self, column_select):
        df_sum = self.df.groupby(['영수일자'])['영수/환급보험료'].sum().reset_index(name='매출액')
        df_sum['구분'] = '손생합계'
        df_sum = df_sum[['구분','영수일자','매출액']]
        df_sum.columns.values[0] = '구분'
        # 구분 고유값만 남기기 (보험종목, 보험회사 등)
        df_present = df_sum.groupby(['구분'])['구분'].count().reset_index(name="개수")
        # 영수일자 고유값만 남기기 (매출액 없어도 일자를 최대로 지정하기 위함)
        df_dates = df_sum.groupby(['영수일자'])['영수일자'].count().reset_index(name="개수")
        # 보험회사 또는 보험종목 개수 만큼 반복문 실행 위해 리스트 제작
        df_category = df_present['구분'].tolist()
        df_sum_year, df_sum_month = self.make_data_running(select=df_sum, dates=df_dates, category=df_category)
        df_insu_year, df_insu_month = self.make_data_basic(column_select)
        df_total_year = pd.concat([df_insu_year, df_sum_year], axis=0)
        df_total_month = pd.concat([df_insu_month, df_sum_month], axis=0)
        return df_total_year, df_total_month

##########################################################################################################################
#####################################     차트 제작 (ChartData 클래스 상속)     ##########################################
##########################################################################################################################
class Charts(ChartData):
    def __init__(self, df):
        super().__init__(df)
        
    # -----------------------------------------------    꺾은선 그래프    ------------------------------------------------------
    def make_chart_line(self, df, title):
        fig_line = pl.graph_objs.Figure()
        # Iterate over unique channels and add a trace for each
        for reference in df['구분'].unique():
            line_data = df[df['구분'] == reference]
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
    
    def make_chart_stacked(self):
        # 차트 제작을 위한 데이터프레임 편집
        df_select = self.df.groupby(['보험종목','영수일자'])['영수/환급보험료'].sum().reset_index(name='매출액')
        df_life = df_select[df_select['보험종목'] == '생명보험'].pivot(index='영수일자',columns='보험종목',values='매출액')
        df_fire = df_select[df_select['보험종목'] == '손해보험'].pivot(index='영수일자',columns='보험종목',values='매출액')
        df_select = pd.merge(df_life, df_fire, on=['영수일자'], how='outer')

        fig = pl.graph_objs.Figure(data=[
            pl.graph_objs.Bar(name='손보', x=df_select.index, y=df_select['손해보험'], marker={'color':'#EF553B'}),
            pl.graph_objs.Bar(name='생보', x=df_select.index, y=df_select['생명보험'], marker={'color':'#636EFA'})
        ])
        # Change the bar mode
        fig.update_layout(barmode='stack')
        return fig

##########################################################################################################################
#################################################     이게 뭘까     ######################################################
##########################################################################################################################
class Year(Charts):
    def __init__(self, df):
        super().__init__(df)
    
    def make_data_year(self):
        category = {'sum':'보험종목','company':'보험회사','product':'상품군','channel':'소속'}
        df_year = pd.DataFrame(columns=['매출액','영수일자'])
        for key, value in category.items():
            df_category = call_data_year(key).rename(columns={'구분':value}).drop(columns=['Unnamed: 0','개수'])
            df_year = pd.merge(df_year, df_category, on=['매출액','영수일자'], how='outer')
        self.df = df_year.rename(columns={'매출액':'영수/환급보험료'})
        return self.df

##########################################################################################################################
############################################     랭킹 데이터 전처리     #################################################
##########################################################################################################################
class Rank:
    def __init__(self, df):
        self.df = df

    # ------------------------------    스타일카드 제작을 위한 필요 컬럼 분류    ------------------------------
    def make_rank(self, columns):
        # 입력 받은 컬럼과 '영수/환급보험료' 칼럼으로 묶고 '영수/환급보혐료' 칼럼은 '매출액' 칼럼으로 변경
        df_result = self.df.groupby(columns)['영수/환급보험료'].sum().reset_index(name='매출액')
        # '매출액' 칼럼을 내림차순으로 정렬
        df_result = df_result.sort_values(by='매출액', ascending=False)
        # '매출액' 칼럼을 숫자 형태로 변환
        df_result['매출액'] = df_result['매출액'].map('{:,.0f}'.format)
        return df_result

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
        df_channel = self.make_rank(columns=['소속'])
        df_result = self.make_rank(reference)
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
    def make_toggles_fa(self, reference, drop, title, form):
        df_fa = self.make_rank(columns=['담당자'])
        df_result = self.make_rank(reference)
        index = [df_fa.iat[i,0] for i in range(5)]
        for a in range(5):
            st.markdown(f"{index[a]} 매출액 상위 {title}")
            df_subrank = df_result[df_result['담당자'].isin([index[a]])].drop(columns=drop)
            if form =='single':
                self.make_card_single(df=df_subrank, number=5)
            if form == 'multiple':
                self.make_card_multiple(df=df_subrank, number=5)

    # ------------------------------------    보험회사별 하위랭킹 제작    ------------------------------------------
    def make_toggles_company(self, reference, drop, title, form):
        df_company = self.make_rank(columns=['보험회사'])
        df_result = self.make_rank(reference)
        index = [df_company.iat[i,0] for i in range(5)]
        for a in range(5):
            st.markdown(f"{index[a]} 매출액 상위 {title}")
            df_subrank = df_result[df_result['보험회사'].isin([index[a]])].drop(columns=drop)
            if form =='single':
                self.make_card_single(df=df_subrank, number=5)
            if form == 'multiple':
                self.make_card_multiple(df=df_subrank, number=5)

    # --------------------------------------    상품군별 하위랭킹 제작    --------------------------------------------
    def make_toggles_category(self, reference, drop, title, form):
        df_result = self.make_rank(reference)
        index = [['보장성','기타(보장성)'],['종신/CI'],['CEO정기보험'],['어린이'],['어린이(태아)'],['운전자'],['단독실손'],['연금','연금저축'],['변액연금']]
        # 하위랭킹 제작을 위한 5개의 스타일카드 제목 생성
        for a in range(len(index)):
            st.markdown(f"{index[a][0]} 매출액 상위 {title}")
            df_subrank = [df_result[df_result['상품군'].isin([index[a][c]])].drop(columns=drop) for c in range(len(index[a]))]
            df_subrank = pd.concat(df_subrank, ignore_index=True)
            if form == 'single':
                self.make_card_single(df=df_subrank, number=5)
            if form == 'multiple':
                self.make_card_multiple(df=df_subrank, number=5)

    # ------------------------------------    보험상품별 하위랭킹 제작    ------------------------------------------
    def make_toggles_product(self, reference, select, drop, form):
        df_result = self.make_rank(reference)
        df_sub = self.make_rank(select)
        for a in range(5):
            st.markdown(f"##### {df_result.iat[a,0]} ({df_result.iat[a,1]})")
            df_subrank = df_sub[df_sub['상품명'].isin([df_result.iat[a,0]])].drop(columns=drop)
            if form == 'single':
                self.make_card_single(df=df_subrank, number=5)
            if form== 'multiple':
                self.make_card_multiple(df=df_subrank, number=5)