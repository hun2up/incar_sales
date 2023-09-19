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
from utils import func_call, func_category, func_insurance
# func_running, fig_linechart, func_dates

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
    df_sep = func_call("sep")
    # 보험종목 및 영수일자 별 매출액
    df_insu = func_category(df_sep, '보험종목')
    # 보험회사 및 영수일자 별 매출액
    df_company = func_category(df_sep, '보험회사')
    # df_insu = ['보험종목','영수/환급일','매출액']
    df_insu = func_insurance(df_sep, df_insu)
    # 매출액 누적
    # df_running_insu = func_running(df_insu)
    # df_running_comapny = func_running(df_company)

    # 함수정의: 누적매출액 계산
    df_company.columns.values[0] = '구분'
    df_temp = df_company.groupby(['구분'])['구분'].count().reset_index(name="개수")
    df_dates = df_company[['영수일자']].copy()
    st.dataframe(df_temp)
    st.dataframe(df_dates)
    '''
    list_running = df_temp['구분'].tolist()
    # 반복문 실행을 위한 구간 선언 
    df_total = pd.DataFrame(columns=['구분','영수일자','매출액'])
    for i in range(len(list_running)):
        # 생명보험이나 손해보험만 남기기
        df_running = df_category[df_category.iloc[:,0] == list_running[i]]
        # 누적매출액 구하기
        for running in range(df_category.shape[0]):
            try:
                df_running.iloc[running+1,2] = df_running.iloc[running+1,2] + df_running.iloc[running,2]
            except:
                pass
        df_total = pd.concat([df_total, df_running], axis=0)
    '''

    ########################################################################################################################
    ##################################################     차트 제작     #####################################################
    ########################################################################################################################
    # fig_line_insurnace = fig_linechart(df_running_insu, '보험종목별 매출액 추이')
    # fig_line_company = fig_linechart(df_running_comapny, '보험회사별 매출액 추이')

    ########################################################################################################################
    ################################################     메인페이지 설정     ###################################################
    ########################################################################################################################
    authenticator.logout('Logout', 'sidebar')
    # 메인페이지 타이틀
    st.header("9월 매출현황")

    # -----------------------------------------------------  차트 노출  ---------------------------------------------------------
    st.markdown("<hr>", unsafe_allow_html=True)
    # st.plotly_chart(fig_line_insurnace, use_container_width=True)
    # st.plotly_chart(fig_line_company, use_container_width=True)

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