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
    start = time.time()

    df_year = pd.DataFrame()
    df_company = pd.DataFrame()
    df_product = pd.DataFrame()
    df_channel = pd.DataFrame()
    
    start_jan = time.time()
    df_jan = call_data("jan")
    instance_jan = Charts(df=df_jan)
    df_jan = pd.DataFrame()
    end_jan = time.time()
    st.write(f"{end_jan - start_jan}")
    start_feb = time.time()
    df_feb = call_data("feb")
    instance_feb = Charts(df=df_feb)
    instance_feb = pd.DataFrame()
    end_feb = time.time()
    st.write(f"{end_feb - start_feb}")
    start_mar = time.time()
    df_mar = call_data("mar")
    instance_mar = Charts(df=df_mar)
    df_mar = pd.DataFrame()
    instance_mar = pd.DataFrame()
    end_mar = time.time()
    st.write(f"{end_mar - start_mar}")
    start_apr = time.time()
    df_apr = call_data("apr")
    instance_apr = Charts(df=df_apr)
    end_apr = time.time()
    st.write(f"{end_apr - start_apr}")
    start_may = time.time()
    df_may = call_data("may")
    instance_may = Charts(df=df_may)
    df_may = pd.DataFrame()
    end_may = time.time()
    st.write(f"{end_may - start_may}")
    start_jun = time.time()
    df_jun = call_data("jun")
    instance_jun = Charts(df=df_jun)
    df_jun = pd.DataFrame()
    instance_jun = pd.DataFrame()
    end_jun = time.time()
    st.write(f"{end_jun - start_jun}")
    start_jul = time.time()
    df_jul = call_data("jul")
    instance_jul = Charts(df=df_jul)
    end_jul = time.time()
    st.write(f"{end_jul - start_jul}")

    '''
    sum_jan, sum_month = instance_chart.make_data_sum(column_select=['보험종목','영수일자'])
    company_jan, company_month = instance_chart.make_data_basic(column_select=['보험회사','영수일자'])
    product_jan, product_month = instance_chart.make_data_basic(column_select=['상품군','영수일자'])
    channel_jan, channel_month = instance_chart.make_data_basic(column_select=['소속','영수일자'])
    df_year = pd.concat([df_year, sum_jan], axis=0)
    df_company = pd.concat([df_company, company_jan], axis=0)
    df_product = pd.concat([df_product, product_jan], axis=0)
    df_channel = pd.concat([df_channel, channel_jan], axis=0)
    
    df_month = call_data("feb")
    instance_chart = Charts(df=df_month)
    sum_feb, sum_month = instance_chart.make_data_sum(column_select=['보험종목','영수일자'])
    company_feb, company_month = instance_chart.make_data_basic(column_select=['보험회사','영수일자'])
    product_feb, product_month = instance_chart.make_data_basic(column_select=['상품군','영수일자'])
    channel_feb, channel_month = instance_chart.make_data_basic(column_select=['소속','영수일자'])
    df_year = pd.concat([df_year, sum_feb], axis=0)
    df_company = pd.concat([df_company, company_feb], axis=0)
    df_product = pd.concat([df_product, product_feb], axis=0)
    df_channel = pd.concat([df_channel, channel_feb], axis=0)
    
    st.dataframe(df_year)
    st.dataframe(df_company)
    st.dataframe(df_product)
    st.dataframe(df_channel)
    '''

    end = time.time()
    st.write(f"시간측정 : {end - start}")