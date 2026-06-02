import streamlit as st
import pandas as pd
import numpy as np
import joblib
import json
import re
import math
import requests
import os
from urllib.parse import urlparse
from datetime import datetime

# ──────────────────────────────────────────
# 페이지 설정
# ──────────────────────────────────────────
st.set_page_config(
    page_title="스미싱/피싱 탐지 시스템",
    page_icon="🛡️",
    layout="wide"
)

# ──────────────────────────────────────────
# 모델 로드
# ──────────────────────────────────────────
@st.cache_resource
def load_model():
    try:
        model        = joblib.load('models/best_model.pkl')
        tfidf        = joblib.load('models/tfidf.pkl')
        feature_cols = joblib.load('models/feature_cols.pkl')
        with open('models/meta.json') as f:
            meta = json.load(f)
        return model, tfidf, feature_cols, meta
    except Exception as e:
        st.error(f"모델 로드 실패: {e}")
        return None, None, None, None

model, tfidf, feature_cols, meta = load_model()

# ──────────────────────────────────────────
# 신뢰 도메인 / TLD / 단축 URL 목록 (v4)
# ──────────────────────────────────────────
TRUSTED_DOMAINS = {
    'google.com', 'youtube.com', 'facebook.com', 'instagram.com',
    'twitter.com', 'microsoft.com', 'apple.com', 'amazon.com',
    'github.com', 'wikipedia.org', 'linkedin.com', 'reddit.com',
    'netflix.com', 'spotify.com', 'twitch.tv',
    'colab.research.google.com', 'docs.google.com', 'drive.google.com',
    'sheets.google.com', 'mail.google.com', 'maps.google.com',
    'gemini.google.com', 'notebooklm.google.com',
    'claude.com', 'claude.ai', 'chatgpt.com', 'openai.com',
    'perplexity.ai', 'midjourney.com', 'canva.com',
    'copilot.microsoft.com', 'gamma.app', 'deepsearch.com',
    'naver.com', 'kakao.com', 'daum.net', 'tistory.com',
    'coupang.com', 'gmarket.co.kr', '11st.co.kr', 'ssg.com',
    'musinsa.com', 'kream.co.kr', '29cm.co.kr', 'zara.com',
    'a-bly.com', 'lookpin.co.kr', 'thisisneverthat.com',
    'oliveyoung.co.kr', 'yes24.com', 'daiso.co.kr',
    'kbstar.com', 'shinhan.com', 'hanabank.com', 'wooribank.com',
    'ibk.co.kr', 'nonghyup.com', 'kakaobank.com', 'toss.im',
    'kebhana.com', 'nhsec.com', 'samsungcard.com',
    'baemin.com', 'yogiyo.co.kr', 'coupangeats.com',
    'mcdonalds.co.kr', 'mega-mgccoffee.com',
    'jtbc.co.kr', 'mbn.co.kr', 'donga.com', 'chosun.com',
    'mk.co.kr', 'hani.co.kr', 'yna.co.kr',
    'severance.healthcare', 'snuh.org', 'anam.kumc.or.kr',
    'dcinside.com', 'fmkorea.com', 'ruliweb.com', 'clien.net',
    'ppomppu.co.kr', 'mlbpark.com', 'inven.co.kr',
    'korail.com', 'jejuair.net', 'airbnb.co.kr', 'airport.co.kr',
    'youtu.be',
    'softonic.com', 'softonic.kr',
    'github.io', 'githubusercontent.com', 'githubassets.com',
    'notion.so', 'slack.com', 'zoom.us', 'figma.com',
    'discord.com', 'telegram.org', 'whatsapp.com',
}

TRUSTED_TLDS = {
    'ac.kr', 'go.kr', 'or.kr', 'edu', 'gov', 'mil', 'ac.uk', 'ac.jp',
}

SHORT_URL_SERVICES = {
    'bit.ly', 'tinyurl.com', 't.co', 'goo.gl', 'ow.ly',
    'han.gl', 'c11.kr', 'nuly.do', 'buly', 'me2.kr',
    'url.kr', 'gg.gg', 'vo.la', 'ibit.ly', 'adf.ly',
    'rb.gy', 'cutt.ly', 'short.io', 'xgo.kr', 'buff.ly',
    'dlvr.it', 'ift.tt', 'fb.me', 'amzn.to',
}

# ──────────────────────────────────────────
# 피처 추출 함수 (v4)
# ──────────────────────────────────────────
def extract_features(url):
    try:
        parsed   = urlparse(url)
        domain   = parsed.netloc.lower().replace('www.', '')
        path     = parsed.path
        query    = parsed.query
        base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

        # 신뢰 도메인 여부
        is_trusted = any(
            domain == td or domain.endswith('.' + td)
            for td in TRUSTED_DOMAINS
        )

        # 신뢰 TLD 여부
        is_trusted_tld = any(
            domain.endswith('.' + tld) or domain == tld
            for tld in TRUSTED_TLDS
        )

        # 단축 URL 여부 (패턴 방식)
        is_short = (
            any(s in domain for s in SHORT_URL_SERVICES) or
            (len(domain.split('.')[0]) <= 6 and
             len(path.strip('/')) <= 8 and
             len(path.strip('/')) >= 3 and
             path.strip('/').isalnum())
        )

        return {
            # 길이 관련
            'url_length':           len(url),
            'base_url_length':      len(base_url),
            'domain_length':        len(domain),
            'path_length':          len(path),
            'query_length':         len(query),
            # 특수문자 (도메인/경로 분리)
            'dot_count':            domain.count('.'),
            'hyphen_count':         domain.count('-'),
            'slash_count':          path.count('/'),
            'at_count':             url.count('@'),
            'percent_count':        query.count('%'),
            'question_count':       url.count('?'),
            'equal_count':          query.count('='),
            'param_count':          len(query.split('&')) if query else 0,
            'path_depth':           len([p for p in path.split('/') if p]),
            # 숫자 관련 (도메인 기준)
            'digit_count':          sum(c.isdigit() for c in domain),
            'digit_ratio':          sum(c.isdigit() for c in domain) / max(len(domain), 1),
            # 구조 관련
            'has_https':            1 if url.startswith('https') else 0,
            'subdomain_count':      max(0, len(domain.split('.')) - 2),
            'has_port':             1 if parsed.port and parsed.port not in (80,443) else 0,
            # 신뢰도 피처 (v4 신규)
            'is_trusted_domain':    1 if is_trusted else 0,
            'is_trusted_tld':       1 if is_trusted_tld else 0,
            # 패턴 관련
            'has_ip':               1 if re.search(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', domain) else 0,
            'is_suspicious_tld':    1 if domain.split('.')[-1] in {
                'tk','ml','ga','cf','gq','xyz','top','click','yachts',
                'uno','work','online','site','website','space'
            } else 0,
            'has_phishing_keyword': 1 if (
                not is_trusted and
                any(k in domain for k in [
                    'login','verify','secure','banking','account-',
                    'update','confirm','alert','suspend'
                ])
            ) else 0,
            'is_short_url':         1 if is_short else 0,
            'has_brand_spoofing':   1 if (
                not is_trusted and
                any(
                    b in domain and
                    not domain.endswith(f'{b}.com') and
                    not domain.endswith(f'{b}.co.kr') and
                    not domain.endswith(f'{b}.net')
                    for b in ['paypal','apple','google','microsoft',
                               'amazon','naver','kakao','toss','kbstar']
                )
            ) else 0,
            'has_korean_smishing':  1 if re.search(r'택배|배송|결제|환급|당첨|무료|인증|지원금|재난', url) else 0,
            'domain_entropy':       -sum(
                (domain.count(c)/len(domain)) * math.log2(domain.count(c)/len(domain))
                for c in set(domain)
            ) if domain else 0,
        }
    except:
        return {}

def tokenize_url(url):
    try:
        parsed = urlparse(url)
        base   = f"{parsed.netloc}{parsed.path}"
        tokens    = re.split(r'[/\.\-\_\?\=\&\:\@\%\+]', base.lower())
        stopwords = {'http','https','www','com','html','php','htm',''}
        return ' '.join([t for t in tokens if len(t) > 2 and t not in stopwords])
    except:
        return ''

def get_suspicious_reasons(features):
    reasons = []
    if features.get('is_trusted_domain'):    reasons.append("🟢 신뢰 도메인 목록에 포함")
    if features.get('is_trusted_tld'):       reasons.append("🟢 신뢰 TLD 사용 (.go.kr .ac.kr 등)")
    if features.get('has_ip'):               reasons.append("🔴 IP 주소 형태의 도메인")
    if features.get('has_brand_spoofing'):   reasons.append("🔴 브랜드명 사칭 의심")
    if features.get('is_suspicious_tld'):    reasons.append("🟠 의심 TLD 사용 (.tk .xyz .online 등)")
    if features.get('at_count', 0) > 0:      reasons.append("🟠 @ 기호 포함")
    if features.get('has_korean_smishing'):  reasons.append("🟠 한국 스미싱 키워드 포함")
    if features.get('is_short_url'):         reasons.append("🟡 단축 URL 사용")
    if features.get('has_phishing_keyword'): reasons.append("🟡 피싱 키워드 포함 (login/verify 등)")
    if features.get('domain_entropy', 0) > 4.5: reasons.append("🟡 도메인 복잡도 높음 (랜덤 문자열)")
    if not features.get('has_https'):        reasons.append("🟡 HTTPS 미사용")
    if features.get('url_length', 0) > 100: reasons.append("🟡 URL 길이 과도하게 긺")
    return reasons

def predict_url(url):
    if not model:
        return None
    features  = extract_features(url)
    token     = tokenize_url(url)
    X_struct  = pd.DataFrame([features])[feature_cols].fillna(0)
    X_tfidf   = tfidf.transform([token])
    from scipy.sparse import hstack, csr_matrix
    X         = hstack([csr_matrix(X_struct.values), X_tfidf])
    prob      = model.predict_proba(X)[0][1]
    pred      = int(prob >= 0.5)
    reasons   = get_suspicious_reasons(features)
    return {
        'url':      url,
        'prob':     round(prob * 100, 1),
        'pred':     pred,
        'reasons':  reasons,
        'features': features
    }

# ──────────────────────────────────────────
# UI
# ──────────────────────────────────────────
st.title("🛡️ 스미싱/피싱 URL 탐지 시스템")
st.markdown("URL을 입력하면 피싱 여부를 실시간으로 분석합니다.")

if meta:
    col1, col2, col3 = st.columns(3)
    col1.metric("사용 모델",    meta.get('best_model', '-'))
    col2.metric("모델 AUC",    f"{meta.get('best_auc', 0):.4f}")
    col3.metric("학습 데이터", "55,300개+")

st.divider()

# 탭 구성
tab1, tab2, tab3 = st.tabs(["🔍 단일 URL 검사", "📋 일괄 검사", "📊 탐지 현황"])

# ──────────────────────────────────────────
# 탭 1. 단일 URL 검사
# ──────────────────────────────────────────
with tab1:
    st.subheader("URL 입력")

    # 예시 버튼 먼저 처리 (session_state 활용)
    if 'example_url' not in st.session_state:
        st.session_state.example_url = ''

    st.markdown("**빠른 예시 테스트:**")
    ex_col1, ex_col2, ex_col3, ex_col4 = st.columns(4)
    if ex_col1.button("피싱 예시 1"):
        st.session_state.example_url = "http://naver-login.tk/verify/account?user=test"
    if ex_col2.button("피싱 예시 2"):
        st.session_state.example_url = "http://kb-bank-secure.xyz/auth/login"
    if ex_col3.button("정상 예시 1"):
        st.session_state.example_url = "https://www.naver.com"
    if ex_col4.button("정상 예시 2"):
        st.session_state.example_url = "https://www.kbstar.com"

    # 예시 버튼 누르면 입력창에 자동 입력
    url_input = st.text_input(
        "검사할 URL을 입력하세요",
        value=st.session_state.example_url,
        placeholder="예: http://naver-login.tk/verify/account"
    )

    # 입력창 바뀌면 session_state 초기화
    if url_input != st.session_state.example_url:
        st.session_state.example_url = url_input

    check_btn = st.button("🔍 검사하기", type="primary")

    if check_btn and url_input:
        with st.spinner("분석 중..."):
            result = predict_url(url_input)

        if result:
            prob = result['prob']

            # 위험도 등급
            if prob >= 80:
                risk_label = "🔴 매우 위험"
                risk_color = "red"
                bg_color   = "#ffebeb"
            elif prob >= 60:
                risk_label = "🟠 위험"
                risk_color = "orange"
                bg_color   = "#fff3e0"
            elif prob >= 40:
                risk_label = "🟡 의심"
                risk_color = "#DAA520"
                bg_color   = "#fffde7"
            else:
                risk_label = "🟢 정상"
                risk_color = "green"
                bg_color   = "#e8f5e9"

            # 결과 표시
            st.markdown(f"""
            <div style='background-color:{bg_color}; padding:20px; border-radius:10px; margin:10px 0'>
                <h2 style='color:{risk_color}; margin:0'>{risk_label}</h2>
                <p style='font-size:18px; margin:5px 0'>피싱 확률: <strong>{prob}%</strong></p>
                <p style='color:gray; margin:0; font-size:13px'>분석 URL: {url_input[:80]}{'...' if len(url_input)>80 else ''}</p>
            </div>
            """, unsafe_allow_html=True)

            # 위험 요인
            if result['reasons']:
                st.markdown("**⚠️ 탐지된 위험 요인:**")
                for r in result['reasons']:
                    st.markdown(f"- {r}")
            else:
                st.success("특별한 위험 요인이 발견되지 않았습니다.")

            # 상세 피처 분석
            with st.expander("📊 상세 피처 분석"):
                feat = result['features']
                f_col1, f_col2, f_col3 = st.columns(3)
                f_col1.metric("URL 길이",      feat.get('url_length', 0))
                f_col2.metric("도메인 길이",   feat.get('domain_length', 0))
                f_col3.metric("HTTPS 여부",    "✅" if feat.get('has_https') else "❌")
                f_col1.metric("도메인 하이픈", feat.get('hyphen_count', 0))
                f_col2.metric("파라미터 수",   feat.get('param_count', 0))
                f_col3.metric("도메인 엔트로피", f"{feat.get('domain_entropy', 0):.2f}")

# ──────────────────────────────────────────
# 탭 2. 일괄 검사
# ──────────────────────────────────────────
with tab2:
    st.subheader("여러 URL 한 번에 검사")
    urls_text = st.text_area(
        "URL 목록 입력 (한 줄에 하나씩)",
        placeholder="https://www.naver.com\nhttp://phish-site.tk/login\nhttps://www.kakao.com",
        height=200
    )

    if st.button("📋 일괄 검사", type="primary"):
        urls = [u.strip() for u in urls_text.splitlines() if u.strip()]
        if urls:
            results = []
            progress = st.progress(0)
            for i, url in enumerate(urls):
                r = predict_url(url)
                if r:
                    results.append({
                        'URL':      url[:60] + ('...' if len(url)>60 else ''),
                        '피싱확률': f"{r['prob']}%",
                        '판정':     '🔴 피싱' if r['pred']==1 else '🟢 정상',
                        '위험요인': len(r['reasons'])
                    })
                progress.progress((i+1)/len(urls))

            df_result = pd.DataFrame(results)
            st.dataframe(df_result, use_container_width=True)

            phish_cnt = sum(1 for r in results if '피싱' in r['판정'])
            c1, c2, c3 = st.columns(3)
            c1.metric("총 검사",   len(results))
            c2.metric("피싱 탐지", phish_cnt,   delta=f"{phish_cnt/len(results)*100:.1f}%")
            c3.metric("정상",      len(results)-phish_cnt)

            csv = df_result.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 결과 다운로드 (CSV)", csv, "results.csv", "text/csv")

# ──────────────────────────────────────────
# 탭 3. 탐지 현황
# ──────────────────────────────────────────
with tab3:
    st.subheader("📊 실시간 피싱 피드 현황")

    if st.button("🔄 최신 피싱 피드 불러오기"):
        with st.spinner("OpenPhish 피드 수집 중..."):
            try:
                resp = requests.get('https://openphish.com/feed.txt', timeout=30)
                urls = [u.strip() for u in resp.text.splitlines() if u.strip()][:50]

                results = []
                prog = st.progress(0)
                for i, url in enumerate(urls):
                    r = predict_url(url)
                    if r:
                        results.append({
                            'URL':      url[:70],
                            '피싱확률': f"{r['prob']}%",
                            '위험도':   '🔴 높음' if r['prob']>=80 else ('🟠 중간' if r['prob']>=60 else '🟡 낮음'),
                        })
                    prog.progress((i+1)/len(urls))

                st.success(f"총 {len(results)}개 URL 분석 완료")
                st.dataframe(pd.DataFrame(results), use_container_width=True)

            except Exception as e:
                st.error(f"피드 수집 실패: {e}")

    st.divider()
    st.markdown("""
    ### 📌 데이터 출처
    | 소스 | 설명 |
    |------|------|
    | PhishTank | 전 세계 커뮤니티 검증 피싱 URL |
    | OpenPhish | 실시간 자동 탐지 피싱 피드 |
    | KISA 2023 | 한국인터넷진흥원 공식 피싱 URL |
    | KISA 2024 | 한국인터넷진흥원 공식 피싱 URL |
    | Majestic Million | 신뢰도 높은 정상 URL |
    """)