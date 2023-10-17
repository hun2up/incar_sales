###########################################################################################################################
################################################     라이브러리 호출     ###################################################
###########################################################################################################################
import streamlit as st
import streamlit_authenticator as stauth
hashed_passwords = stauth.Hasher(['XXX']).generate()
import yaml
from yaml.loader import SafeLoader
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)
from utils import hide_st_style, style_metric_cards, call_data, make_sidebar
from utils import Charts, Toggles
from utils import month_dict

###########################################################################################################################
################################################     인증페이지 설정     ###################################################
###########################################################################################################################
# ---------------------------------------------    페이지 레이아웃 설정    --------------------------------------------------
st.set_page_config(page_title="실적관리 대시보드", layout='wide')

# ----------------------------------------    Google Sheet 데이터베이스 호출    ---------------------------------------------
# 9월 실적현황 SHEET 호출
month = "sep"
this_month = month_dict[month]
df_month = call_data(month)

# -----------------------------------------------------  사이드바  ---------------------------------------------------------
# 사이드바 헤더
st.sidebar.header("원하는 옵션을 선택하세요")
# 사이드바 제작
insurance = make_sidebar(df_month,'보험종목') # 월도 선택 사이드바
company = make_sidebar(df_month,'보험회사') # 보험사 선택 사이드바
theme = make_sidebar(df_month,'상품군') # 입사연차 선택 사이드바
channel = make_sidebar(df_month,'소속') # 소속부문 선택 사이드바
# 데이터와 사이드바 연결
df_month = df_month.query(
    "보험종목 == @insurance & 보험회사 == @company & 상품군 == @theme & 소속 == @channel"
)

# -------------------------------------------------  인증페이지 삽입  -------------------------------------------------------
# 인증모듈 기본설정
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

# 로그인창 노출
name, authentication_status, username = authenticator.login('Login', 'main')
# 사이드바에 로그아웃 버튼 추가
authenticator.logout('Logout', 'sidebar')

# 인증상태 검증
if authentication_status == None:
    st.warning('아이디와 패스워드를 입력해주세요')
if authentication_status == False:
    st.error('아이디와 패스워드를 확인해주세요')
if authentication_status:
    ##########################################################################################################################
    ##############################################     메인페이지 타이틀     ##################################################
    ##########################################################################################################################
    hide_st_style()
    st.header(f"{this_month} 매출현황 추이 (그래프)")

    ##########################################################################################################################
    ##################################################     차트 (현황)     ####################################################
    ##########################################################################################################################
    instance_chart = Charts(df=df_month)

    sum_year, sum_month = instance_chart.make_data_sum(column_select=['보험종목','영수일자'])
    st.plotly_chart(instance_chart.make_chart_line(df=sum_month, title='보험종목별 매출액 추이'), use_container_width=True)

    # -----------------------------------------  보험사별 매출액, 상품군별 매출액  ----------------------------------------------
    fig_line_company, fig_line_product = st.columns(2)
    company_year, company_month = instance_chart.make_data_basic(column_select=['보험회사','영수일자'])
    product_year, product_month = instance_chart.make_data_basic(column_select=['상품군','영수일자'])
    fig_line_company.plotly_chart(instance_chart.make_chart_line(df=company_month, title='보험회사별 매출액 추이'), use_container_width=True) # 보험회사별 매출액
    fig_line_product.plotly_chart(instance_chart.make_chart_line(df=product_month, title='상품군별 매출액 추이'), use_container_width=True) # 상품군별 매출액
    
    # ---------------------------------------  소속부문별 매출액, 입사연차별 매출액  ---------------------------------------------
    fig_line_channel, fig_line_career = st.columns(2)
    channel_year, channel_month = instance_chart.make_data_basic(column_select=['소속','영수일자'])
    fig_line_channel.plotly_chart(instance_chart.make_chart_line(df=channel_month, title='소속부문별 매출액 추이') ,use_container_width=True)

    ##########################################################################################################################
    ##############################################     스타일 카드 (랭킹)     #################################################
    ##########################################################################################################################
    st.markdown('---')
    st.markdown("## 주요 매출액 순위")
    style_metric_cards()

    # --------------------------------------------------  부문별 랭킹  -----------------------------------------------------------
    # 메인랭킹 (소속부문 매출액 순위)
    instance_channel = Toggles(df=df_month)
    st.markdown('---') # 구분선
    channel = st.columns([2,1,1,1]) # 컬럼 나누기
    channel[0].markdown('#### 부문 매출액 순위') # 제목
    instance_channel.make_card_single(df=instance_channel.make_rank(columns=['소속']), number=6)
    # 세부랭킹 (토글)
    if channel[1].toggle('부문별 매출액 상위 FA'):
        instance_channel.make_toggles_channel(reference=['소속','담당자','파트너'], title='FA', form='multiple')
    if channel[2].toggle('부문별 매출액 상위 보험회사'):
        instance_channel.make_toggles_channel(reference=['소속','보험회사'], title='보험회사', form='single')
    if channel[3].toggle('부문별 매출액 상위 보험상품'):
        instance_channel.make_toggles_channel(reference=['소속','상품명','보험회사'], title='보험상품', form='multiple')

    # --------------------------------------------------  FA별  -----------------------------------------------------------
    # 메인랭킹 (FA 매출액 순위)
    instance_fa = Toggles(df=df_month)
    st.markdown('---')
    fa = st.columns([2,1,1,1])
    fa[0].markdown("#### 매출액 상위 FA")
    instance_fa.make_card_multiple(df=instance_fa.make_rank(columns=['담당자','파트너']), number=5)
    # 세부랭킹(토글)
    if fa[3].toggle('매출액 상위 FA 주요 판매상품'):
        instance_fa.make_toggles_fa(reference=['담당자','담당자코드','상품명','보험회사'], drop=['담당자','담당자코드'], title='보험상품', form='multiple')

    # --------------------------------------------------  보험회사별  -----------------------------------------------------------
    # 메인랭킹 (소속부문 매출액 순위)
    instance_company = Toggles(df=df_month)
    st.markdown('---') # 구분선
    company = st.columns([2,1,1,1]) # 컬럼 나누기
    company[0].markdown('#### 매출액 상위 보험회사') # 제목
    instance_company.make_card_single(df=instance_company.make_rank(columns=['보험회사']), number=5)
    # 세부랭킹 (토글)
    if company[1].toggle('보험회사별 매출액 상위 지점'):
        instance_company.make_toggles_company(reference=['보험회사','파트너','소속'], drop=['보험회사'], title='지점', form='multiple')
    if company[2].toggle('보험회사별 매출액 상위 FA'):
        instance_company.make_toggles_company(reference=['보험회사','담당자코드','담당자','파트너'], drop=['보험회사','담당자코드'], title='FA', form='multiple')
    if company[3].toggle('보험회사별 매출액 상위 보험상품'):
        instance_company.make_toggles_company(reference=['보험회사','상품명','상품군'], drop=['보험회사'], title='보험상품', form='multiple')            

    # --------------------------------------------------  상품군별  -----------------------------------------------------------
    # 메인랭킹 (상품군 매출액 순위)
    instance_category = Toggles(df=df_month)
    st.markdown('---') # 구분선
    category = st.columns([2,1,1,1])
    category[0].markdown('#### 매출액 상위 상품군')
    instance_category.make_card_single(df=instance_category.make_rank(columns=['상품군']), number=5)
    # 세부랭킹 (토글)
    if category[1].toggle('상품군별 매출액 상위 지점'):
        instance_category.make_toggles_category(reference=['파트너','소속','상품군'], drop=['상품군'], title='지점', form='multiple')
    if category[2].toggle('상품군별 매출액 상위 FA'):
        instance_category.make_toggles_category(reference=['담당자','담당자코드','파트너','상품군'], drop=['담당자코드','상품군'], title='FA', form='multiple')
    if category[3].toggle('상품군별 매출액 상위 보험상품'):
        instance_category.make_toggles_category(reference=['상품명','보험회사','상품군'], drop=['상품군'], title='보험상품', form='multiple')
    
    # --------------------------------------------------  보험상품별  -----------------------------------------------------------      
    # 메인랭킹 (보험상품 매출액 순위)
    instance_product = Toggles(df=df_month)
    st.markdown('---') # 구분선
    prod = st.columns([2,1,1,1]) # 컬럼 나누기
    prod[0].markdown("#### 매출액 상위 보험상품") # 제목
    instance_product.make_card_multiple(df=instance_product.make_rank(columns=['상품명','보험회사']), number=5)
    # 세부랭킹 (토글)
    if prod[2].toggle('보험상품별 매출액 상위 지점'):
        instance_product.make_toggles_product(reference=['상품명','보험회사'], select=['상품명','파트너','소속'], drop=['상품명'], form='multiple')
    if prod[3].toggle('보험상품별 매출액 상위 FA'):
        instance_product.make_toggles_product(reference=['상품명','보험회사'], select=['상품명','담당자코드','담당자','파트너'], drop=['상품명','담당자코드'], form='multiple')