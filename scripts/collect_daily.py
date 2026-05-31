"""
GitHub Actions에서 매일 자동 실행되는 피싱 데이터 수집 스크립트
수집된 데이터는 data/ 폴더에 저장되고 자동 커밋됨
"""

import requests
import pandas as pd
import os
from datetime import datetime

DATA_DIR = 'data'
os.makedirs(DATA_DIR, exist_ok=True)

def collect_openphish():
    """OpenPhish 실시간 피드 수집"""
    try:
        resp = requests.get('https://openphish.com/feed.txt', timeout=30)
        urls = [u.strip() for u in resp.text.splitlines() if u.strip()]
        df   = pd.DataFrame({'url': urls, 'label': 1, 'date': datetime.now().strftime('%Y-%m-%d')})
        path = f'{DATA_DIR}/openphish_latest.csv'
        df.to_csv(path, index=False)
        print(f"✅ OpenPhish: {len(df)}개 수집 → {path}")
        return df
    except Exception as e:
        print(f"❌ OpenPhish 수집 실패: {e}")
        return pd.DataFrame()

def collect_phishtank():
    """PhishTank 대안 피드 수집"""
    try:
        url  = "https://raw.githubusercontent.com/mitchellkrogza/Phishing.Database/master/phishing-links-ACTIVE.txt"
        resp = requests.get(url, timeout=60)
        urls = [u.strip() for u in resp.text.splitlines() if u.strip() and not u.startswith('#')]
        df   = pd.DataFrame({'url': urls[:5000], 'label': 1, 'date': datetime.now().strftime('%Y-%m-%d')})
        path = f'{DATA_DIR}/phishtank_latest.csv'
        df.to_csv(path, index=False)
        print(f"✅ PhishTank: {len(df)}개 수집 → {path}")
        return df
    except Exception as e:
        print(f"❌ PhishTank 수집 실패: {e}")
        return pd.DataFrame()

def update_log(openphish_cnt, phishtank_cnt):
    """수집 로그 업데이트"""
    log_path = f'{DATA_DIR}/collection_log.csv'
    new_row  = pd.DataFrame([{
        'date':          datetime.now().strftime('%Y-%m-%d %H:%M'),
        'openphish_cnt': openphish_cnt,
        'phishtank_cnt': phishtank_cnt,
        'total':         openphish_cnt + phishtank_cnt
    }])

    if os.path.exists(log_path):
        log = pd.read_csv(log_path)
        log = pd.concat([log, new_row], ignore_index=True)
    else:
        log = new_row

    log.to_csv(log_path, index=False)
    print(f"✅ 수집 로그 업데이트 완료")

if __name__ == '__main__':
    print(f"=== 피싱 데이터 자동 수집 시작: {datetime.now().strftime('%Y-%m-%d %H:%M')} ===")
    op = collect_openphish()
    pt = collect_phishtank()
    update_log(len(op), len(pt))
    print(f"=== 수집 완료: 총 {len(op)+len(pt)}개 ===")
