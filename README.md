# 🛡️ 스미싱/피싱 URL 탐지 시스템

URL 기반 머신러닝 피싱 탐지 시스템입니다.

## 데모

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app-url.streamlit.app)

## 프로젝트 구조

```
├── app.py                          # Streamlit 메인 앱
├── requirements.txt                # 의존성
├── models/                         # 학습된 모델
│   ├── best_model.pkl
│   ├── tfidf.pkl
│   ├── feature_cols.pkl
│   └── meta.json
├── data/                           # 수집된 데이터
│   ├── phishtank_latest.csv        # 매일 자동 업데이트
│   └── collection_log.csv          # 수집 이력
├── scripts/
│   └── collect_daily.py            # 자동 수집 스크립트
└── .github/workflows/
    └── collect_data.yml            # GitHub Actions
```

## 데이터 출처

| 소스 | 설명 | 업데이트 |
|------|------|----------|
| PhishTank | 커뮤니티 검증 피싱 URL | 매일 자동 |
| KISA 2023/2024 | 한국인터넷진흥원 공식 데이터 | 연 1회 |
| Majestic Million | 정상 URL | 수동 |
| PhishStats | 실시간 피싱 URL | 매일 자동 |

## 탐지 피처 (26개)

### URL 구조 피처
- base_url_length: 파라미터 제외 URL 길이
- url_length, domain_length, path_length, query_length

### 특수문자 피처 (도메인/경로 분리)
- dot_count, hyphen_count: 도메인 기준
- slash_count: 경로 기준
- at_count, percent_count, question_count, equal_count
- param_count: 파라미터 개수
- path_depth: 경로 깊이

### 보안 피처
- has_https, has_ip, has_port
- subdomain_count, digit_count, digit_ratio

### 패턴 피처
- is_suspicious_tld (.tk .xyz .ml 등)
- has_phishing_keyword (도메인에서만 탐지)
- is_short_url, has_brand_spoofing
- has_korean_smishing (택배/환급/당첨 등)
- domain_entropy

## 모델 성능 (v3)

| 지표 | 점수 |
|------|------|
| ROC-AUC | 0.9972 |
| Precision | 0.99+ |
| Recall | 0.98+ |
| F1-Score | 0.98+ |

## v1 → v2 → v3 개선 과정

| 버전 | 주요 변경 |
|------|----------|
| v1 | 기본 모델 (URL 전체 기준 피처 22개) |
| v2 | KISA 데이터 추가, 정상 데이터 다양화 |
| v3 | 피처 도메인/경로 분리, 오탐 개선 (26개) |

## 로컬 실행

```bash
pip install -r requirements.txt
streamlit run app.py
```
