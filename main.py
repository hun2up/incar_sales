###########################################################################################################################
################################################     라이브러리 호출     ###################################################
###########################################################################################################################
import pandas as pd
import streamlit as st
import streamlit_authenticator as stauth
hashed_passwords = stauth.Hasher(['XXX']).generate()
import yaml
from yaml.loader import SafeLoader
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)
from utils import hide_st_style, call_data_year

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
    year_sum = call_data_year("sum").rename(columns={'구분':'보험종목'}).drop(columns=['Unnamed: 0','개수'])
    year_company = call_data_year("company").rename(columns={'구분':'보험회사'}).drop(columns=['Unnamed: 0','개수'])
    year_product = call_data_year("product").rename(columns={'구분':'상품군'}).drop(columns=['Unnamed: 0','개수'])
    year_channel = call_data_year("channel").rename(columns={'구분':'소속'}).drop(columns=['Unnamed: 0','개수'])
    year_merge = pd.merge(year_sum, year_company, on=['매출액','영수일자'], how='outer')
    year_merge = pd.merge(year_merge, year_product, on=['매출액','영수일자'], how='outer')
    year_merge = pd.merge(year_merge, year_channel, on=['매출액','영수일자'], how='outer')
    st.dataframe(year_merge)
