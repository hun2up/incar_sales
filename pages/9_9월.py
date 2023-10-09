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
from utils import fn_call, fn_sidebar, fn_visualization, fn_ranking, fn_insurance, fig_linechart
from utils import month_dict

###########################################################################################################################
################################################     인증페이지 설정     ###################################################
###########################################################################################################################
# ---------------------------------------------    페이지 레이아웃 설정    --------------------------------------------------
st.set_page_config(page_title="실적관리 대시보드", layout='wide')

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
    dfc_insu = fn_visualization(df_sep, ['보험종목','영수일자'], 'chart') # 보험종목별 매출액
    dfc_company = fn_visualization(df_sep, ['보험회사','영수일자'], 'chart') # 보험회사별 매출액
    dfc_product = fn_visualization(df_sep, ['상품군','영수일자'], 'chart') # 상품군별 매출액
    dfc_channel = fn_visualization(df_sep, ['소속','영수일자'], 'chart') # 소속부문별 매출액
    dfc_insu = fn_insurance(df_sep, dfc_insu) # 보험종목별(손생) 매출액 데이터에 합계 데이터 삽입: ['보험종목','영수/환급일','매출액']

    # ----------------------------------------------------  랭킹  -----------------------------------------------------------
    dfr_chn = fn_visualization(df_sep, ['소속'], 'rank') # 소속부문 매출액 순위
    dfr_fa = fn_visualization(df_sep, ['파트너','담당자코드','담당자'], 'rank') # FA 매출액 순위
    dfr_fa = dfr_fa.drop(columns='담당자코드')
    dfr_com = fn_visualization(df_sep, ['보험회사'], 'rank') # 보험회사 매출액 순이
    dfr_cat = fn_visualization(df_sep, ['상품군'], 'rank') # 상품군 매출액 순위
    dfr_prod = fn_visualization(df_sep, ['상품명','보험회사'], 'rank') # 보험상품 매출액 순위

    # 상품군별 상위 TOP5 보험상품
    dfr_cat_prod = fn_visualization(df_sep, ['상품명','보험회사','상품군'], 'rank')
    dfr_cat_cover = dfr_cat_prod[dfr_cat_prod['상품군'].isin(['보장성','기타(보장성)'])].drop(columns='상품군') # 보장성
    dfr_cat_whole = dfr_cat_prod[dfr_cat_prod['상품군'].isin(['종신/CI'])].drop(columns='상품군') # 종신/CI
    dfr_cat_ceo = dfr_cat_prod[dfr_cat_prod['상품군'].isin(['CEO정기보험'])].drop(columns='상품군') # CEO정기보험
    dfr_cat_child = dfr_cat_prod[dfr_cat_prod['상품군'].isin(['어린이'])].drop(columns='상품군') # 어린이
    dfr_cat_fetus = dfr_cat_prod[dfr_cat_prod['상품군'].isin(['어린이(태아)'])].drop(columns='상품군') # 어린이(태아)
    dfr_cat_driver = dfr_cat_prod[dfr_cat_prod['상품군'].isin(['운전자'])].drop(columns='상품군') # 운전자
    dfr_cat_real = dfr_cat_prod[dfr_cat_prod['상품군'].isin(['단독실손'])].drop(columns='상품군') # 단독실손
    dfr_cat_pension = dfr_cat_prod[dfr_cat_prod['상품군'].isin(['연금'])].drop(columns='상품군') # 연금
    dfr_cat_vul = dfr_cat_prod[dfr_cat_prod['상품군'].isin(['변액연금'])].drop(columns='상품군') # 변액연금

    # 매출액 상위 FA별 상위 TOP5 보험상품
    dfr_fa_prod = fn_visualization(df_sep, ['상품명','보험회사','담당자코드','담당자'], 'rank')
    dfr_fa1 = dfr_fa_prod[dfr_fa_prod['담당자'].isin([dfr_fa_prod.iat[0, 2]])].drop(columns=['담당자코드','담당자']) # 매출액 1위
    dfr_fa2 = dfr_fa_prod[dfr_fa_prod['담당자'].isin([dfr_fa_prod.iat[1, 2]])].drop(columns=['담당자코드','담당자']) # 매출액 2위
    dfr_fa3 = dfr_fa_prod[dfr_fa_prod['담당자'].isin([dfr_fa_prod.iat[2, 2]])].drop(columns=['담당자코드','담당자']) # 매출액 3위
    dfr_fa4 = dfr_fa_prod[dfr_fa_prod['담당자'].isin([dfr_fa_prod.iat[3, 2]])].drop(columns=['담당자코드','담당자']) # 매출액 4위
    dfr_fa5 = dfr_fa_prod[dfr_fa_prod['담당자'].isin([dfr_fa_prod.iat[4, 2]])].drop(columns=['담당자코드','담당자']) # 매축액 5위

    #########################################################################################################################
    ##################################################     차트 제작     #####################################################
    #########################################################################################################################
    # --------------------------------------------  추이 그래프(꺾은선) 제작  -------------------------------------------------
    fig_line_insurnace = fig_linechart(dfc_insu, '보험종목별 매출액 추이')
    fig_line_company = fig_linechart(dfc_company, '보험회사별 매출액 추이')
    fig_line_product = fig_linechart(dfc_product, '상품군별 매출액 추이')
    fig_line_channel = fig_linechart(dfc_channel, '소속부문별 매출액 추이')

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

    # 소속부문 매출액 순위는 금액 단위가 커서 '원' 생략
    st.markdown('---')
    st.markdown("##### 소속부문 매출액 순위")
    chn = st.columns(6)
    for i in range(6):
        chn[i].metric(dfr_chn.iat[i, 0], dfr_chn.iat[i, 1])

    tgl_chn_fa = st.toggle("각 부문별 매출액 상위 TOP5 FA")
    tgl_chn_com = st.toggle("각 부문별 매출액 상위 TOP5 보험회사")
    tgl_chn_prd = st.toggle("각 부문별 매출액 상위 TOP5 보험상품")
    
    st.markdown('---')
    fa = st.columns(5)
    rfa = st.columns(5)
    fa[0].markdown("##### 매출액 상위 TOP5 (FA)")
    fn_ranking(dfr_fa, 'multiple', rfa)
    if fa[4].toggle("매출액 상위 FA 주요 판맴상품"):
        st.write("상품군별 매출액 상위 TOP5 보험상품 (보장성)")
        fa1 = st.columns(5)
        fn_ranking(dfr_fa1, 'multiple', fa1)
        st.write("상품군별 매출액 상위 TOP5 보험상품 (보장성)")
        fa2 = st.columns(5)
        fn_ranking(dfr_fa2, 'multiple', fa2)
        st.write("상품군별 매출액 상위 TOP5 보험상품 (보장성)")
        fa3 = st.columns(5)
        fn_ranking(dfr_fa3, 'multiple', fa3)
        st.write("상품군별 매출액 상위 TOP5 보험상품 (보장성)")
        fa4 = st.columns(5)
        fn_ranking(dfr_fa4, 'multiple', fa4)
        st.write("상품군별 매출액 상위 TOP5 보험상품 (보장성)")
        fa5 = st.columns(5)
        fn_ranking(dfr_fa5, 'multiple', fa5)
        

    st.markdown('---')
    st.markdown("##### 매출액 상위 TOP5 (보험회사)")
    com = st.columns(5)
    fn_ranking(dfr_com, 'single', com)

    st.markdown('---')
    cat = st.columns(5)
    rcat = st.columns(5)
    cat[0].markdown("##### 매출액 상위 TOP5 (상품군)")
    fn_ranking(dfr_cat, 'single', rcat)
    if cat[4].toggle("상품군별 매출액 순위"):
        st.write("상품군별 매출액 상위 TOP5 보험상품 (보장성)")
        cat_cover = st.columns(5)
        fn_ranking(dfr_cat_cover, 'multiple', cat_cover)
        st.write("상품군별 매출액 상위 TOP5 보험상품 (종신/CI)")
        cat_whole = st.columns(5)
        fn_ranking(dfr_cat_whole, 'multiple', cat_whole)
        st.write("상품군별 매출액 상위 TOP5 보험상품 (CEO정기보험)")
        cat_ceo = st.columns(5)
        fn_ranking(dfr_cat_ceo, 'multiple', cat_ceo)
        st.write("상품군별 매출액 상위 TOP5 보험상품 (어린이)")
        cat_child = st.columns(5)
        fn_ranking(dfr_cat_child, 'multiple', cat_child)
        st.write("상품군별 매출액 상위 TOP5 보험상품 (어린이(태아))")
        cat_fetus = st.columns(5)
        fn_ranking(dfr_cat_fetus, 'multiple', cat_fetus)
        st.write("상품군별 매출액 상위 TOP5 보험상품 (운전자)")
        cat_driver = st.columns(5)
        fn_ranking(dfr_cat_driver, 'multiple', cat_driver)
        st.write("상품군별 매출액 상위 TOP5 보험상품 (단독실손)")
        cat_real = st.columns(5)
        fn_ranking(dfr_cat_real, 'multiple', cat_real)
        st.write("상품군별 매출액 상위 TOP5 보험상품 (연금)")
        cat_pension = st.columns(5)
        fn_ranking(dfr_cat_pension, 'multiple', cat_pension)
        st.write("상품군별 매출액 상위 TOP5 보험상품 (변액연금)")
        cat_vul = st.columns(5)
        fn_ranking(dfr_cat_vul, 'multiple', cat_vul)

    st.markdown('---')
    st.markdown("##### 매출액 상위 TOP5 (보험상품)")
    prod = st.columns(5)
    fn_ranking(dfr_prod, 'multiple', prod)

    '''
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
    '''
            
    # style_metric_cards()