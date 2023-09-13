########################################################################################################################
################################################     라이브러리 호출     ###################################################
########################################################################################################################
import pandas as pd
import streamlit as st
from utils import load_data, fig_linechart

########################################################################################################################
################################################     자료 전처리     ######################################################
########################################################################################################################
# ---------------------------------------    Google Sheet 데이터베이스 호출    ----------------------------------------------
# 출석부 데이터베이스 호출 (교육과정수료현황) & 컬럼 삭제 (번호)
df_august = load_data(st.secrets["aug_url"]).drop(columns=['SUNAB_PK','납입회차','납입월도','영수유형','확정자','확정일','환산월초','인정실적','실적구분','이관일자','확정유형','계약상태','최초등록일'])
# df_august['영수/환급일'] = pd.to_datetime(df_august['영수/환급일'])
df_august['영수/환급보험료'] = pd.to_numeric(df_august['영수/환급보험료'].str.replace(",",""))
df_insurance = df_august.groupby(['보험종목']).count()
df_insurance = df_august.groupby(['보험종목','영수/환급일'])['영수/환급보험료'].sum().reset_index(name='매출액')
df_fire = df_insurance.drop(df_insurance[df_insurance.iloc[:,0] == '생명보험'].index)
df_life = df_insurance.drop(df_insurance[df_insurance.iloc[:,0] == '손해보험'].index)

for running in range(df_fire.shape[0]):
    try:
        df_fire.iloc[running+1,2] = df_fire.iloc[running+1,2] + df_fire.iloc[running,2]
    except:
        pass

st.dataframe(df_fire)


'''
list_linechart[0]: dataframe (df_stat, df_trnd)
list_linechart[1]: 참조 컬럼 (소속부문, 입사연차, 과정명)
list_linechart[2]: 데이터 (신청인원, 신청누계, 수료인원, 수료누계, 수료율, IMO신청률 등)
list_linechart[3]: df_apply: '월' / df_attend: '날짜'
list_linechart[4]: 차트 제목
'''

list_line_insuarance = [df_insurance, '보험종목', '매출액', '영수/환급일', '보험종목별 매출액 추이']
fig_line_insurnace = fig_linechart(list_line_insuarance)

########################################################################################################################
################################################     메인페이지 설정     ###################################################
########################################################################################################################
# authenticator.logout('Logout', 'sidebar')
# 메인페이지 타이틀
st.header("8월 매출현황")

# -----------------------------------------------------  차트 노출  ---------------------------------------------------------
st.markdown("<hr>", unsafe_allow_html=True)
st.dataframe(df_insurance)
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