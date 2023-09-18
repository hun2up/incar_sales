########################################################################################################################
################################################     라이브러리 호출     ###################################################
########################################################################################################################
import pandas as pd
import streamlit as st
import streamlit_authenticator as stauth
hashed_passwords = stauth.Hasher(['XXX']).generate()
import yaml
from yaml.loader import SafeLoader
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)
from utils import load_data, func_insurance, func_running, fig_linechart

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
    df_august = load_data(st.secrets["sep_url"])
    # df_insu = ['보험종목','영수/환급일','매출액']
    df_insu = func_insurance(df_august)
    # 매출액 누적
    # df_running = func_running(df_insu)

    st.dataframe(df_insu)
    # 반복문 실행을 위한 구간 선언 
    insu = ['생명보험','손해보험','손생합계']
    df_total = pd.DataFrame(columns=['보험종목','영수일자','매출액'])
    for i in range(3):
        # 생명보험이나 손해보험만 남기기
        st.text(f'i is : {insu[i]}')
        df_running = df_insu.drop(df_insu[df_insu.iloc[:,0] != insu[i]].index)
        st.dataframe(df_insu[df_insu.iloc[:,0] == insu[i]])
        # 누적매출액 구하기
        for running in range(df_running.shape[0]):
            try:
                df_running.iloc[running+1,2] = df_running.iloc[running+1,2] + df_running.iloc[running,2]
            except:
                pass
        df_total = pd.concat([df_total, df_running], axis=0)

    ########################################################################################################################
    ##################################################     차트 제작     #####################################################
    ########################################################################################################################
    list_line_insuarance = [df_total, '보험종목', '매출액', '영수일자', '보험종목별 매출액 추이']
    fig_line_insurnace = fig_linechart(list_line_insuarance)

    ########################################################################################################################
    ################################################     메인페이지 설정     ###################################################
    ########################################################################################################################
    authenticator.logout('Logout', 'sidebar')
    # 메인페이지 타이틀
    st.header("9월 매출현황")

    # -----------------------------------------------------  차트 노출  ---------------------------------------------------------
    st.markdown("<hr>", unsafe_allow_html=True)
    st.dataframe(df_insu)
    st.dataframe(df_running)
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