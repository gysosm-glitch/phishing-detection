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
│   ├── openphish_latest.csv        # 매일 자동 업데이트
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
| OpenPhish | 실시간 피싱 피드 | 매일 자동 |
| KISA 2023/2024 | 한국인터넷진흥원 공식 데이터 | 연 1회 |
| Majestic Million | 정상 URL | 수동 |

## 탐지 피처 (22개)

- URL 길이, 도메인 길이, 경로 길이
- 특수문자 개수 (점, 하이픈, 슬래시 등)
- HTTPS 여부, IP 주소 도메인 여부
- 의심 TLD 여부 (.tk .xyz 등)
- 브랜드 사칭 여부
- 한국 스미싱 키워드 포함 여부
- URL 엔트로피

## 모델 성능

| 지표 | 점수 |
|------|------|
| ROC-AUC | 0.99+ |
| Precision | 0.99+ |
| Recall | 0.99+ |
| F1-Score | 0.99+ |

## 로컬 실행

```bash
pip install -r requirements.txt
streamlit run app.py
```
