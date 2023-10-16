###########################################################################################################################
################################################     라이브러리 호출     ###################################################
###########################################################################################################################
import time
import streamlit as st
import streamlit_authenticator as stauth
hashed_passwords = stauth.Hasher(['XXX']).generate()
import yaml
from yaml.loader import SafeLoader
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)
from utils import hide_st_style, style_metric_cards, call_data, make_sidebar, make_chartdata, sum_lnf, make_chart_line, make_rankdata, make_cards, make_toggles, make_rank_channel, make_rank_company, make_rank_category, make_rank_product, make_subtoggle
from utils import Toggles
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
df_month = call_data(month)

# -----------------------------------------------------  사이드바  ---------------------------------------------------------
# 사이드바 헤더
st.sidebar.header("원하는 옵션을 선택하세요")
# 사이드바 제작
insurance = make_sidebar(df_month,'보험종목') # 월도 선택 사이드바
company = make_sidebar(df_month,'보험회사') # 보험사 선택 사이드바
theme = make_sidebar(df_month,'상품군') # 입사연차 선택 사이드바
channel = make_sidebar(df_month,'소속') # 소속부문 선택 사이드바
# 데이터와 사이드바 연결
df_month = df_month.query(
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
# 사이드바에 로그아웃 버튼 추가
authenticator.logout('Logout', 'sidebar')

# 인증상태 검증
if authentication_status == None:
    st.warning('아이디와 패스워드를 입력해주세요')
if authentication_status == False:
    st.error('아이디와 패스워드를 확인해주세요')
if authentication_status:
    # fn_peformance(df_month, this_month)
    start_all = time.time()
    ##########################################################################################################################
    ##############################################     메인페이지 타이틀     ##################################################
    ##########################################################################################################################
    hide_st_style()
    st.header(f"{this_month} 매출현황 추이 (그래프)")

    ##########################################################################################################################
    ##################################################     차트 (현황)     ####################################################
    ##########################################################################################################################
    start_chart = time.time()

    # ----------------------------------------------  생손매출액 (꺾은선)  -----------------------------------------------------
    dfc_insu = make_chartdata(df_month, ['보험종목','영수일자']) # 보험종목별 매출액
    df_insu = sum_lnf(df_month, dfc_insu) # 보험종목별(손생) 매출액 데이터에 합계 데이터 삽입: ['보험종목','영수/환급일','매출액']
    st.plotly_chart(make_chart_line(df_insu, '보험종목별 매출액 추이'), use_container_width=True)

    # -----------------------------------------  보험사별 매출액, 상품군별 매출액  ----------------------------------------------
    fig_line_company, fig_line_prod = st.columns(2)
    dfc_company = make_chartdata(df_month, ['보험회사','영수일자']) # 보험회사별 매출액
    fig_line_company.plotly_chart(make_chart_line(dfc_company, '보험회사별 매출액 추이'), use_container_width=True)
    dfc_prod = make_chartdata(df_month, ['상품군','영수일자']) # 상품군별 매출액
    fig_line_prod.plotly_chart(make_chart_line(dfc_prod, '상품군별 매출액 추이'), use_container_width=True)

    # ---------------------------------------  소속부문별 매출액, 입사연차별 매출액  ---------------------------------------------
    fig_line_chn, r2_c2 = st.columns(2)
    dfc_chn = make_chartdata(df_month, ['소속','영수일자']) # 소속부문별 매출액
    fig_line_chn.plotly_chart(make_chart_line(dfc_chn, '소속부문별 매출액 추이'), use_container_width=True)

    end_chart = time.time()
    st.write(f"시간측정(차트) : {end_chart - start_chart} sec")

    
    ##########################################################################################################################
    ##############################################     스타일 카드 (랭킹)     #################################################
    ##########################################################################################################################
    st.markdown('---')
    st.markdown("## 주요 매출액 순위")
    style_metric_cards()

    start_rank = time.time()
    # --------------------------------------------------  부문별 랭킹  -----------------------------------------------------------
    start_rchn = time.time()
    # 메인랭킹 (소속부문 매출액 순위)
    dfr_chn = make_rankdata(df_month, ['소속']) 
    chn = st.columns([2,1,1,1])\
    
    chn[0].markdown("#### 부문 매출액 순위")
    rchn = st.columns(6)
    for i in range(6):
        rchn[i].metric(dfr_chn.iat[i, 0], dfr_chn.iat[i, 1] + '원')
    # 세부랭킹 (토글)
    # Rank_instance = Rank(df_month, ['소속', '담당자', '파트너'])
    # dfr_chn_fa = Rank_instance.make_rankdata_class()
    dfr_chn_fa = make_rankdata(df_month, ['소속','담당자','파트너']) # 소속부문별 매출액 상위 FA
    lst_chn_fa = make_rank_channel(dfr_chn, dfr_chn_fa, "FA")
    dfr_chn_com = make_rankdata(df_month, ['소속','보험회사']) # 소속부문별 매출액 상위 보험회사
    lst_chn_com = make_rank_channel(dfr_chn, dfr_chn_com, "보험회사")
    dfr_chn_prod = make_rankdata(df_month, ['소속','상품명','보험회사']) # 소속부문별 매출액 상위 보험상품
    lst_chn_prod = make_rank_channel(dfr_chn, dfr_chn_prod, "보험상품")
    if chn[1].toggle("부문별 매출액 상위 FA (수정)"):
        st.markdown("##### 부문별 매출액 상위 FA")
        make_toggles(lst_chn_fa, 'multiple')
    if chn[2].toggle("부문별 매출액 상위 보험회사 (수정)"):
        st.markdown("##### 부문별 매출액 상위 보험회사")
        make_toggles(lst_chn_com, 'single')
    if chn[3].toggle("부문별 매출액 상위 보험상품 (수정)"):
        st.markdown("##### 부문별 매출액 상위 보험상품")
        make_toggles(lst_chn_prod, 'multiple')
    end_rchn = time.time()
    st.write(f"시간측정(랭킹-부문) : {end_rchn - start_rchn} sec")

    start_rfa = time.time()
    # --------------------------------------------------  FA별  -----------------------------------------------------------
    # 메인랭킹 (FA 매출액 순위)
    dfr_fa = make_rankdata(df_month, ['담당자코드','담당자','파트너']) 
    dfr_fa = dfr_fa.drop(columns='담당자코드')
    dfr_fa_prod = make_rankdata(df_month, ['담당자','담당자코드','상품명','보험회사'])
    dfr_fa_prod = dfr_fa_prod.drop(columns=['담당자','담당자코드'])
    st.markdown('---')
    fa = st.columns([2,1,1,1])
    fa[0].markdown("#### 매출액 상위 FA")
    make_cards(dfr_fa, 'multiple')
    # 세부랭킹 (토글)
    if fa[3].toggle("매출액 상위 FA 주요 판매상품 "):
        st.markdown("##### 매출액 상위 FA 주요 판매상품")
        for c in range(5):
            st.write(dfr_fa.iat[c,1] + ' (' + dfr_fa.iat[c,0] + ')')
            fa_prod = st.columns(5)
            for i in range(5):
                try: fa_prod[i].metric(dfr_fa_prod.iat[i,0] + ' (' + dfr_fa_prod.iat[i,1] + ')', dfr_fa_prod.iat[i, 2] + '원') 
                except: pass
    end_rfa = time.time()
    st.write(f"시간측정(랭킹-FA) : {end_rfa - start_rfa} sec")

    # --------------------------------------------------  보험회사별  -----------------------------------------------------------
    start_rcom = time.time()
    # 메인랭킹 (보험회사 매출액 순위)
    dfr_com = make_rankdata(df_month, ['보험회사']) 
    st.markdown('---') # 구분선
    com = st.columns([2,1,1,1]) # 컬럼 나누기
    com[0].markdown("#### 매출액 상위 보험회사") # 제목
    make_cards(dfr_com, 'single') # 메인랭킹 노출
    # 세부랭킹 (토글)
    company = []
    dfr_com_ptn = make_rankdata(df_month, ['보험회사','파트너','소속']) # 보험회사별 매출액 상위 지점
    company.append(make_rank_company(dfr_com, dfr_com_ptn, ['보험회사']))
    dfr_com_fa = make_rankdata(df_month, ['보험회사','담당자코드','담당자','파트너']) # 보험회사별 매출액 상위 FA
    company.append(make_rank_company(dfr_com, dfr_com_fa, ['보험회사','담당자코드']))
    dfr_com_prod = make_rankdata(df_month, ['보험회사','상품명','상품군']) # 보험회사별 매출액 상위 보험상품
    company.append(make_rank_company(dfr_com, dfr_com_prod, ['보험회사']))
    # make_subtoggle(3, com, company, ['보험회사별 매출액 상위 지점', '보험회사별 매출액 상위 FA', '보험회사별 매출액 상위 보험상품'])
    
    if com[1].toggle("보험회사별 매출액 상위 지점 (수정)"): # 보험회사별 매출액 상위 지점
        st.markdown("##### 보험회사별 매출액 상위 지점")
        make_toggles(company[0], 'multiple')
    if com[2].toggle("보험회사별 매출액 상위 FA (수정)"): # 보험회사별 매출액 상위 FA
        st.markdown("##### 보험회사별 매출액 상위 FA")
        make_toggles(company[1], 'multiple')
    if com[3].toggle("보험회사별 매출액 상위 보험상품 (수정)"): # 보험회사별 매출액 상위 보험상품
        st.markdown("##### 보험회사별 매출액 상위 보험상품")
        make_toggles(company[2], 'multiple')
    end_rcom = time.time()
    st.write(f"시간측정(랭킹-보험회사(수정)) : {end_rcom - start_rcom} sec")

    # --------------------------------------------------  상품군별  -----------------------------------------------------------
    start_rcat = time.time()
    # 메인랭킹 (상품군 매출액 순위)
    dfr_cat = make_rankdata(df_month, ['상품군']) 
    st.markdown('---')
    cat = st.columns([2,1,1,1])
    cat[0].markdown("#### 매출액 상위 상품군")
    make_cards(dfr_cat, 'single')
    # 세부랭킹 (토글)
    lst_cat = []
    dfr_cat_ptn = make_rankdata(df_month, ['파트너','소속','상품군']) # 상품군별 매출액 상위 지점
    lst_cat.append(make_rank_category(dfr_cat_ptn, '지점'))
    dfr_cat_fa = make_rankdata(df_month, ['담당자','담당자코드','파트너','상품군']) # 상품군별 매출액 상위 FA
    dfr_cat_fa = dfr_cat_fa.drop(columns='담당자코드')
    lst_cat.append(make_rank_category(dfr_cat_fa, 'FA'))
    dfr_cat_prod = make_rankdata(df_month, ['상품명','보험회사','상품군']) # 상품군별 매출액 상위 보험상품
    lst_cat.append(make_rank_category(dfr_cat_prod, '보험상품'))
    make_subtoggle(3, cat, lst_cat, ['상품군별 매출액 상위 지점', '상품군별 매출액 상위 FA', '상품군별 매출액 상위 보험상품'])
    end_rcat = time.time()
    st.write(f"시간측정(랭킹-상품군) : {end_rcat - start_rcat} sec")
    
    # --------------------------------------------------  보험상품별  -----------------------------------------------------------      
    start_rprod = time.time()
    # 메인랭킹 (보험상품 매출액 순위)
    instance_product = Toggles(df=df_month)
    st.markdown('---') # 구분선
    prod = st.columns([2,1,1,1]) # 컬럼 나누기
    prod[0].markdown("#### 매출액 상위 보험상품") # 제목
    instance_product.make_card_multiple(df=instance_product.make_rankdata_class(columns=['상품명','보험회사']), number=5)
    # 세부랭킹 (토글)
    if prod[2].toggle('보험상품별 매출액 상위 지점'):
        instance_product.make_toggles_product(columns=['상품명','보험회사'], select=['상품명','파트너','소속'], drop=['상품명'])
    if prod[3].toggle('보험상품별 매출액 상위 FA'):
        instance_product.make_toggles_product(columns=['상품명','보험회사'], select=['상품명','담당자코드','담당자','파트너'], drop=['상품명','담당자코드'])

    end_rprod = time.time()
    st.write(f"시간측정(랭킹-보험상품(수정)) : {end_rprod - start_rprod} sec")
    end_rank = time.time()
    st.write(f"시간측정(랭킹) : {end_rank - start_rank} sec")
    end_all = time.time()
    st.write(f"시간측정(전체) : {end_all - start_all} sec")