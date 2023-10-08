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
from utils import fn_call, fn_sidebar, fn_category, fn_insurance, fn_running, fig_linechart, style_metric_cards
from utils import month_dict

###########################################################################################################################
################################################     인증페이지 설정     ###################################################
###########################################################################################################################
# ---------------------------------------------    페이지 레이아웃 설정    --------------------------------------------------
st.set_page_config(page_title="실적관리 대시보드", layout='wide')

# ----------------------------------------    Google Sheet 데이터베이스 호출    ---------------------------------------------
# 9월 실적현황 SHEET 호출
month = "sep"
this_month = month_dict[month]
df_sep = fn_call(month)

# -----------------------------------------------------  사이드바  ---------------------------------------------------------
# 사이드바 헤더
st.sidebar.header("원하는 옵션을 선택하세요")
# 사이드바 제작
insurance = fn_sidebar(df_sep,'보험종목') # 월도 선택 사이드바
company = fn_sidebar(df_sep,'보험회사') # 보험사 선택 사이드바
theme = fn_sidebar(df_sep,'상품군') # 입사연차 선택 사이드바
channel = fn_sidebar(df_sep,'소속') # 소속부문 선택 사이드바
# 데이터와 사이드바 연결
df_sep = df_sep.query(
    "보험종목 == @insurance & 보험회사 == @company & 상품군 == @theme & 소속 == @channel"
)

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

# 인증상태 검증
if authentication_status == None:
    st.warning('아이디와 패스워드를 입력해주세요')
if authentication_status == False:
    st.error('아이디와 패스워드를 확인해주세요')
if authentication_status:
    ##########################################################################################################################
    ################################################     자료 전처리     ######################################################
    ##########################################################################################################################
    # -------------------------------------------  매출액 기준 기본 전처리  ----------------------------------------------------
    # 보험종목별 매출액
    df_insu = fn_category(df_sep, '보험종목')
    # 보험회사별 매출액
    df_company = fn_category(df_sep, '보험회사')
    # 상품군별 매출액
    df_product = fn_category(df_sep, '상품군')
    # 소속부문별 매출액
    df_channel = fn_category(df_sep, '소속')
    # 보험종목별(손생) 매출액 데이터에 합계 데이터 삽입: ['보험종목','영수/환급일','매출액']
    df_insu = fn_insurance(df_sep, df_insu)

    # ----------------------------------------------------  랭킹  -----------------------------------------------------------
    # 매출액 순위 (소속부문별)
    df_rank_chn = df_sep.groupby(['소속'])['영수/환급보험료'].sum().reset_index(name='매출액').sort_values(by='매출액', ascending=False)
    df_rank_chn['매출액'] = df_rank_chn['매출액'].map('{:,.0f}'.format)
    
    # 매출액 상위 TOP5 (FA)
    df_rank_fa = df_sep.groupby(['파트너','담당자코드','담당자'])['영수/환급보험료'].sum().reset_index(name='매출액').sort_values(by='매출액', ascending=False)
    df_rank_fa['매출액'] = df_rank_fa['매출액'].map('{:,.0f}'.format)

    df_rank_product_fa = df_sep.groupby(['파트너','담당자코드','담당자','보험회사','상품명'])['영수/환급보험료'].sum().reset_index(name='매출액').sort_values(by='매출액', ascending=False)
    df_rank_product_fa['매출액'] = df_rank_product_fa['매출액'].map('{:,.0f}'.format)

    # 매출액 상위 TOP5 (보험회사)
    df_rank_company = df_sep.groupby(['보험회사'])['영수/환급보험료'].sum().reset_index(name='매출액').sort_values(by='매출액', ascending=False)
    df_rank_company['매출액'] = df_rank_company['매출액'].map('{:,.0f}'.format)
    
    # 매출액 상위 TOP5 (상품군)
    df_rank_product_group = df_sep.groupby(['상품군'])['영수/환급보험료'].sum().reset_index(name='매출액').sort_values(by='매출액', ascending=False)
    df_rank_product_group['매출액'] = df_rank_product_group['매출액'].map('{:,.0f}'.format)

    # 매출액 상위 TOP5 (보험상품)
    df_rank_product = df_sep.groupby(['상품군','보험회사','상품명'])['영수/환급보험료'].sum().reset_index(name='매출액').sort_values(by='매출액', ascending=False)
    df_rank_product['매출액'] = df_rank_product['매출액'].map('{:,.0f}'.format)

    # 상품군별 상위 TOP5 보험상품
    # 보장성
    df_product_cover = df_rank_product[df_rank_product['상품군'].isin(['보장성','기타(보장성)'])]
    # 종신/CI
    df_product_whole = df_rank_product[df_rank_product['상품군'].isin(['종신/CI'])]
    # CEO정기보험
    df_product_ceo = df_rank_product[df_rank_product['상품군'].isin(['CEO정기보험'])]
    # 어린이
    df_product_child = df_rank_product[df_rank_product['상품군'].isin(['어린이'])]
    # 어린이(태아)
    df_product_fetus = df_rank_product[df_rank_product['상품군'].isin(['어린이(태아)'])]
    # 운전자
    df_product_driver = df_rank_product[df_rank_product['상품군'].isin(['운전자'])]
    # 단독실손
    df_product_real = df_rank_product[df_rank_product['상품군'].isin(['단독실손'])]
    # 연금
    df_product_pension = df_rank_product[df_rank_product['상품군'].isin(['연금'])]
    # 변액연금
    df_product_vul = df_rank_product[df_rank_product['상품군'].isin(['변액연금'])]

    # 매출액 상위 FA별 상위 TOP5 보험상품
    df_fa1 = df_rank_product_fa[df_rank_product_fa['담당자'].isin([df_rank_product_fa.iat[0, 2]])]
    df_fa2 = df_rank_product_fa[df_rank_product_fa['담당자'].isin([df_rank_product_fa.iat[1, 2]])]
    df_fa3 = df_rank_product_fa[df_rank_product_fa['담당자'].isin([df_rank_product_fa.iat[2, 2]])]
    df_fa4 = df_rank_product_fa[df_rank_product_fa['담당자'].isin([df_rank_product_fa.iat[3, 2]])]
    df_fa5 = df_rank_product_fa[df_rank_product_fa['담당자'].isin([df_rank_product_fa.iat[4, 2]])]

    # ----------------------------------------  일별 누적 매출액 데이터 산출  ----------------------------------------------------
    # 보험종목별 누적매출액
    df_running_insu = fn_running(df_insu)
    # 보험회사별 누적매출액
    df_running_comapny = fn_running(df_company)
    # 상품군별 누적매출액
    df_running_product = fn_running(df_product)
    # 소속부문별 누적매출액
    df_running_channel = fn_running(df_channel)

    #########################################################################################################################
    ##################################################     차트 제작     #####################################################
    #########################################################################################################################
    # --------------------------------------------  추이 그래프(꺾은선) 제작  -------------------------------------------------
    fig_line_insurnace = fig_linechart(df_running_insu, '보험종목별 매출액 추이')
    fig_line_company = fig_linechart(df_running_comapny, '보험회사별 매출액 추이')
    fig_line_product = fig_linechart(df_running_product, '상품군별 매출액 추이')
    fig_line_channel = fig_linechart(df_running_channel, '소속부문별 매출액 추이')

    ##########################################################################################################################
    ################################################     메인페이지 설정     ##################################################
    ##########################################################################################################################
    # 사이드바에 로그아웃 버튼 추가
    authenticator.logout('Logout', 'sidebar')
    # 메인페이지 타이틀
    st.header(f"{this_month} 매출현황")

    # -----------------------------------------------------  차트 노출  ---------------------------------------------------------
    st.markdown("<hr>", unsafe_allow_html=True)
    # 첫번째 행 (생손매출액)
    st.plotly_chart(fig_line_insurnace, use_container_width=True)
    # 두번째 행 (보험사별, 상품군별 매출액)
    r1_c1, r1_c2 = st.columns(2)
    r1_c1.plotly_chart(fig_line_company, use_container_width=True)
    r1_c2.plotly_chart(fig_line_product, use_container_width=True)
    # 세번째 행 (소속부문별, 입사연차별 매출액)
    r2_c1, r2_c2 = st.columns(2)
    r2_c1.plotly_chart(fig_line_channel, use_container_width=True)

    # ----------------------------------------------------  랭킹  -----------------------------------------------------------
    st.markdown('---')
    st.markdown("#### 전체 현황 요약")

    st.write("소속부문별 매출액 순위")
    toggle_state = st.checkbox("보이기")
    chn = st.columns(6)
    if toggle_state:
        for i in range(6):
            chn[i].metric(df_rank_chn.iat[i, 0], df_rank_chn.iat[i, 1])
    else:
        st.write("숨기기")

    st.write("매출액 상위 TOP5 (FA)")
    fa = st.columns(5)
    for i in range(5):
        fa[i].metric(df_rank_fa.iat[i, 2] + ' (' + df_rank_fa.iat[i, 0] + ')', df_rank_fa.iat[i, 3] + '원')

    st.write("매출액 상위 TOP5 (보험회사)")
    company = st.columns(5)
    for i in range(5):
        company[i].metric(df_rank_company.iat[i, 0], df_rank_company.iat[i, 1] + '원')

    st.write("매출액 상위 TOP5 (상품군)")
    product_group = st.columns(5)
    for i in range(5):
        product_group[i].metric(df_rank_product_group.iat[i, 0], df_rank_product_group.iat[i, 1] + '원')

    st.markdown("---")
    st.markdown("#### 전체 현황 요약")

    st.write("상품군별 매출액 상위 TOP5 보험상품 (보장성)")
    product_cover = st.columns(5)
    for i in range(5):
        product_cover[i].metric(df_product_cover.iat[i, 1] + ' (' + df_product_cover.iat[i, 2] + ')', df_product_cover.iat[i, 3] + '원')

    st.write("상품군별 매출액 상위 TOP5 보험상품 (종신/CI)")
    product_whole = st.columns(5)
    for i in range(5):
        product_whole[i].metric(df_product_whole.iat[i, 1] + ' (' + df_product_whole.iat[i, 2] + ')', df_product_whole.iat[i, 3] + '원')

    st.write("상품군별 매출액 상위 TOP5 보험상품 (CEO정기보험)")
    product_ceo = st.columns(5)
    for i in range(5):
        product_ceo[i].metric(df_product_ceo.iat[i, 1] + ' (' + df_product_ceo.iat[i, 2] + ')', df_product_ceo.iat[i, 3] + '원')

    st.write("상품군별 매출액 상위 TOP5 보험상품 (어린이)")
    product_child = st.columns(5)
    for i in range(5):
        product_child[i].metric(df_product_child.iat[i, 1] + ' (' + df_product_child.iat[i, 2] + ')', df_product_child.iat[i, 3] + '원')

    st.write("상품군별 매출액 상위 TOP5 보험상품 (어린이(태아))")
    product_fetus = st.columns(5)
    for i in range(5):
        product_fetus[i].metric(df_product_fetus.iat[i, 1] + ' (' + df_product_fetus.iat[i, 2] + ')', df_product_fetus.iat[i, 3] + '원')

    st.write("상품군별 매출액 상위 TOP5 보험상품 (운전자)")
    product_driver = st.columns(5)
    for i in range(5):
        product_driver[i].metric(df_product_driver.iat[i, 1] + ' (' + df_product_driver.iat[i, 2] + ')', df_product_driver.iat[i, 3] + '원')

    st.write("상품군별 매출액 상위 TOP5 보험상품 (단독실손)")
    product_real = st.columns(5)
    for i in range(5):
        product_real[i].metric(df_product_real.iat[i, 1] + ' (' + df_product_real.iat[i, 2] + ')', df_product_real.iat[i, 3] + '원')

    st.write("상품군별 매출액 상위 TOP5 보험상품 (연금)")
    product_pension = st.columns(5)
    for i in range(5):
        product_pension[i].metric(df_product_pension.iat[i, 1] + ' (' + df_product_pension.iat[i, 2] + ')', df_product_pension.iat[i, 3] + '원')

    st.write("상품군별 매출액 상위 TOP5 보험상품 (변액연금)")
    product_vul = st.columns(5)
    for i in range(5):
        product_vul[i].metric(df_product_vul.iat[i, 1] + ' (' + df_product_vul.iat[i, 2] + ')', df_product_vul.iat[i, 3] + '원')

    st.markdown("---")
    st.write("#### 매출액 상위 FA별 판매상품 TOP5")

    st.write(df_fa1.iat[0,2] + ' (' + df_fa1.iat[0,0] + ')')
    fa1 = st.columns(5)
    for i in range(5):
        try:
            fa1[i].metric(df_fa1.iat[i,3] + ' (' + df_fa1.iat[i,4], df_fa1.iat[i,5] + '원')
        except:
            break
    
    st.write(df_fa2.iat[0,2] + ' (' + df_fa2.iat[0,0] + ')')
    fa2 = st.columns(5)
    for i in range(5):
        try:
            fa2[i].metric(df_fa2.iat[i,3] + ' (' + df_fa2.iat[i,4], df_fa2.iat[i,5] + '원')
        except:
            break
            
    st.write(df_fa3.iat[0,2] + ' (' + df_fa3.iat[0,0] + ')')
    fa3 = st.columns(5)
    for i in range(5):
        try:
            fa3[i].metric(df_fa3.iat[i,3] + ' (' + df_fa3.iat[i,4], df_fa3.iat[i,5] + '원')
        except:
            break

    st.write(df_fa4.iat[0,2] + ' (' + df_fa4.iat[0,0] + ')')
    fa4 = st.columns(5)
    for i in range(5):
        try:
            fa4[i].metric(df_fa4.iat[i,3] + ' (' + df_fa4.iat[i,4], df_fa4.iat[i,5] + '원')
        except:
            break

    st.write(df_fa5.iat[0,2] + ' (' + df_fa5.iat[0,0] + ')')
    fa5 = st.columns(5)
    for i in range(5):
        try:
            fa5[i].metric(df_fa5.iat[i,3] + ' (' + df_fa5.iat[i,4], df_fa5.iat[i,5] + '원')
        except:
            break
            
    style_metric_cards()


    ###########################################################################################################################
    ###########################################     stremalit 워터마크 숨기기     ##############################################
    ###########################################################################################################################
    hide_st_style = """
                    <style>
                    #MainMenu {visibility: hidden;}
                    footer {visibility: hidden;}
                    header {visibility: hidden;}
                    </style>
                    """
    st.markdown(hide_st_style, unsafe_allow_html=True)