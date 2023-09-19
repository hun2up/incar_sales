########################################################################################################################
################################################     라이브러리 호출     ###################################################
########################################################################################################################
import streamlit as st
import streamlit_authenticator as stauth
hashed_passwords = stauth.Hasher(['XXX']).generate()
import yaml
from yaml.loader import SafeLoader
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)
from utils import fn_call, fn_sidebar, fn_category, fn_insurance, fn_running, fig_linechart
from utils import month_dict

########################################################################################################################
################################################     인증페이지 설정     ###################################################
########################################################################################################################
# ---------------------------------------    Google Sheet 데이터베이스 호출    ----------------------------------------------
# 출석부 데이터베이스 호출 (교육과정수료현황) & 컬럼 삭제 (번호)
month = "may"
this_month = month_dict[month]
df_may = fn_call(month)

# -----------------------------------------------------  사이드바  ---------------------------------------------------------
# 사이드바 헤더
st.sidebar.header("원하는 옵션을 선택하세요")
#사이드바 제작
insurance = fn_sidebar(df_may,'보험종목') # 월도 선택 사이드바
company = fn_sidebar(df_may,'보험회사') # 보험사 선택 사이드바
channel = fn_sidebar(df_may,'소속') # 소속부문 선택 사이드바
theme = fn_sidebar(df_may,'상품군') # 입사연차 선택 사이드바
# 데이터와 사이드바 연결
df_may = df_may.query(
    "보험종목 == @insurance & 보험회사 == @company & 소속 == @channel & 상품군 == @theme"
)

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
    # 보험종목 및 영수일자 별 매출액
    df_insu = fn_category(df_may, '보험종목')
    # 보험회사 및 영수일자 별 매출액
    df_company = fn_category(df_may, '보험회사')
    # df_insu = ['보험종목','영수/환급일','매출액']
    df_insu = fn_insurance(df_may, df_insu)
    # 매출액 누적
    df_running_insu = fn_running(df_insu)
    df_running_comapny = fn_running(df_company)

    ########################################################################################################################
    ##################################################     차트 제작     #####################################################
    ########################################################################################################################
    fig_line_insurnace = fig_linechart(df_running_insu, '보험종목별 매출액 추이')
    fig_line_company = fig_linechart(df_running_comapny, '보험회사별 매출액 추이')

    ########################################################################################################################
    ################################################     메인페이지 설정     ###################################################
    ########################################################################################################################
    authenticator.logout('Logout', 'sidebar')
    # 메인페이지 타이틀
    st.header(f"{this_month} 매출현황")

    # -----------------------------------------------------  차트 노출  ---------------------------------------------------------
    st.markdown("<hr>", unsafe_allow_html=True)
    st.plotly_chart(fig_line_insurnace, use_container_width=True)
    st.plotly_chart(fig_line_company, use_container_width=True)

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