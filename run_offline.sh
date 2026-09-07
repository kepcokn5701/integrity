#!/usr/bin/env bash
# 폐쇄망(인터넷 없음)에서 wheels 디렉터리만으로 설치·구동
set -e
cd "$(dirname "$0")"
python3 -m venv venv
source venv/bin/activate
pip install --no-index --find-links=wheels -r requirements.txt
streamlit run app.py --server.address 0.0.0.0 --server.port 8502 --server.headless true
