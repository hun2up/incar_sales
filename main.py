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
from utils import hide_st_style
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
    for key in month_dict:
        st.write(key)