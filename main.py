###########################################################################################################################
################################################     라이브러리 호출     ###################################################
###########################################################################################################################
import time
import pandas as pd
import streamlit as st
import streamlit_authenticator as stauth
hashed_passwords = stauth.Hasher(['XXX']).generate()
import yaml
from yaml.loader import SafeLoader
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)
from utils import hide_st_style, call_data_year
from utils import Charts, Year

###########################################################################################################################
################################################     인증페이지 설정     ###################################################
###########################################################################################################################
# ---------------------------------------------    페이지 레이아웃 설정    --------------------------------------------------
st.set_page_config(page_title="실적관리 대시보드", layout='wide')

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
    st.header("2023년 연간 매출현황 종합 (그래프)")

    ##########################################################################################################################
    ##################################################     차트 (현황)     ####################################################
    ##########################################################################################################################
    start_after = time.time()
    merge_year_test = pd.DataFrame()
    instance_year_test = Year(merge_year_test)
    instance_year_test.make_data_year()

    # ---------------------------------------------------  손생 매출액  ----------------------------------------------------
    sum_trash, sum_year_test = instance_year_test.make_data_basic(column_select=['보험종목','영수일자'])
    st.plotly_chart(instance_year_test.make_chart_line(df=sum_year_test, title='보험종목별 매출액 추이'), use_container_width=True)

    # -----------------------------------------  보험사별 매출액, 상품군별 매출액  ----------------------------------------------
    fig_line_company_test, fig_line_product_test = st.columns(2)
    company_trash, company_year_test = instance_year_test.make_data_basic(column_select=['보험회사','영수일자'])
    product_trash, product_year_test = instance_year_test.make_data_basic(column_select=['상품군','영수일자'])
    fig_line_company_test.plotly_chart(instance_year_test.make_chart_line(df=company_year_test, title='보험회사별 매출액 추이'), use_container_width=True) # 보험회사별 매출액
    fig_line_product_test.plotly_chart(instance_year_test.make_chart_line(df=product_year_test, title='상품군별 매출액 추이'), use_container_width=True) # 상품군별 매출액
    
    # ---------------------------------------  소속부문별 매출액, 입사연차별 매출액  ---------------------------------------------
    fig_line_channel_test, fig_line_career_test = st.columns(2)
    channel_trash, channel_year_test = instance_year_test.make_data_basic(column_select=['소속','영수일자'])
    fig_line_channel_test.plotly_chart(instance_year_test.make_chart_line(df=channel_year_test, title='소속부문별 매출액 추이') ,use_container_width=True)
    
    end_after = time.time()
    st.write(f"after : {end_after - start_after}")