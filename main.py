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
from utils import hide_st_style, call_data
from utils import Charts, Toggles
from utils import month_dict

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
    # st.header(f"{this_month} 매출현황 추이 (그래프)")

    ##########################################################################################################################
    ##################################################     차트 (현황)     ####################################################
    ##########################################################################################################################
    month = ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec']
    start = time.time()
    df_year = pd.DataFrame()
    df_company = pd.DataFrame()
    df_product = pd.DataFrame()
    df_channel = pd.DataFrame()
    for i in month:
        st.write(i)
        # df_month = call_data(i)
    
    # st.dataframe(df_month)

    '''
    for key in month_dict:
        df_month = call_data(key)
        instance_chart = Charts(df=df_month)
        sum_year, sum_month = instance_chart.make_data_sum(column_select=['보험종목','영수일자'])
        company_year, company_month = instance_chart.make_data_basic(column_select=['보험회사','영수일자'])
        product_year, product_month = instance_chart.make_data_basic(column_select=['상품군','영수일자'])
        channel_year, channel_month = instance_chart.make_data_basic(column_select=['소속','영수일자'])
        df_year = pd.concat([df_year, sum_year], axis=0)
        df_company = pd.concat([df_company, company_year], axis=0)
        df_product = pd.concat([df_product, product_year], axis=0)
        df_channel = pd.concat([df_channel, channel_year], axis=0)
    
    st.dataframe(df_year)
    st.dataframe(df_company)
    st.dataframe(df_product)
    st.dataframe(df_channel)
    '''

    end = time.time()
    st.write(f"시간측정 : {end - start}")