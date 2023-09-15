########################################################################################################################
################################################     라이브러리 호출     ###################################################
########################################################################################################################
import pandas as pd
import streamlit as st
import streamlit_authenticator as stauth
hashed_passwords = stauth.Hasher(['incar_edu']).generate()
import yaml
from yaml.loader import SafeLoader
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)
from utils import load_data, df_insurance, func_running, fig_linechart

########################################################################################################################
################################################     인증페이지 설정     ###################################################
########################################################################################################################
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

name, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status == None:
    st.warning('아이디와 패스워드를 입력해주세요')
if authentication_status == False:
    st.error('아이디와 패스워드를 확인해주세요')
if authentication_status:
    ########################################################################################################################
    ################################################     자료 전처리     ######################################################
    ########################################################################################################################
    # ---------------------------------------    Google Sheet 데이터베이스 호출    ----------------------------------------------
    # 출석부 데이터베이스 호출 (교육과정수료현황) & 컬럼 삭제 (번호)
    df_august = load_data(st.secrets["sep_url"]).drop(columns=['SUNAB_PK','납입회차','납입월도','영수유형','확정자','확정일','환산월초','인정실적','실적구분','이관일자','확정유형','계약상태','최초등록일'])
    # df_insu = ['보험종목','영수/환급일','매출액']
    df_insu = df_insurance(df_august)
    df_insu.rename(columns={'영수/환급일':'영수일자'}, inplace=True)
    # 매출액 누적
    df_running = func_running(df_insu)

    ########################################################################################################################
    ##################################################     차트 제작     #####################################################
    ########################################################################################################################
    list_line_insuarance = [df_running, '보험종목', '매출액', '영수일자', '보험종목별 매출액 추이']
    fig_line_insurnace = fig_linechart(list_line_insuarance)

    ########################################################################################################################
    ################################################     메인페이지 설정     ###################################################
    ########################################################################################################################
    authenticator.logout('Logout', 'sidebar')
    # 메인페이지 타이틀
    st.header("9월 매출현황")

    # -----------------------------------------------------  차트 노출  ---------------------------------------------------------
    st.markdown("<hr>", unsafe_allow_html=True)
    st.plotly_chart(fig_line_insurnace, use_container_width=True)

    ########################################################################################################################
    ###########################################     stremalit 워터마크 숨기기     ##############################################
    ########################################################################################################################
    hide_st_style = """
                    <style>
                    #MainMenu {visibility: hidden;}
                    footer {visibility: hidden;}
                    header {visibility: hidden;}
                    </style>
                    """
    st.markdown(hide_st_style, unsafe_allow_html=True)