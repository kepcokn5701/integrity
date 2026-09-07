# 청렴 나침반 — 인터랙티브 청렴 사례집 (프로토타입)

기존 청렴 챗봇과 **별개로**, 청렴·행동강령 **사례집**을 대화하듯 탐색하는 도구입니다.
상담을 대신하는 것이 아니라, 사례집에서 필요한 한 건을 3초 만에 찾아주는 것이 목적입니다.
사내 폐쇄망에서 단독 구동됩니다.
**외부 통신이 전혀 없습니다** — LLM API, 텔레메트리, CDN 호출 모두 사용하지 않습니다.

```
브라우저(사내 PC) ──HTTP──▶ Streamlit(app.py) ──▶ cases.json (로컬 파일)
```

## 두 가지 형태

같은 `cases.json`을 쓰는 두 개의 구현이 있습니다. 용도에 맞게 고르세요.

| | **A. 단일 HTML** | **B. Streamlit** |
|---|---|---|
| 파일 | `index.html` | `app.py` |
| 실행 | 더블클릭 | 서버 구동 |
| 설치물 | **없음** | Python + streamlit |
| 용도 | 시연·회람·의사결정용 | 실제 서비스 |
| 한계 | 사용 로그 수집 불가 | 서버 필요 |

**시연·검토 단계라면 A로 충분합니다.** 42 KB 파일 하나라 메일로 보내거나 USB로
반입해서 바로 열 수 있고, 폐쇄망 보안 검토도 훨씬 간단합니다. 이후 실제 도입이
결정되고 사용 통계·문의 이력이 필요해지는 시점에 B로 넘어가면 됩니다.

## 구성

| 파일 | 역할 |
|---|---|
| `cases.json` | 사례 데이터 — **담당자가 직접 수정하는 곳 (단일 출처)** |
| `build_html.py` | `cases.json` → `index.html` 생성기 |
| `index.html` | **[A]** 생성 결과물. 의존성 0 · 외부 통신 0 |
| `app.py` | **[B]** 화면 + 검색 엔진 (단일 파일) |
| `.streamlit/config.toml` | **[B]** 폐쇄망 기본 설정(텔레메트리 차단 등) |
| `Dockerfile` / `run_offline.sh` | **[B]** 반입·배포용 |

검색은 양쪽 모두 외부 라이브러리 없이 문자 n-gram TF-IDF로 구현되어 있습니다
(형태소 분석기 불필요). 동일한 알고리즘이라 검색 결과도 동일합니다.

## 실행

**A. 단일 HTML**

```bash
python build_html.py     # cases.json 수정 후 다시 실행하면 반영됨
```

생성된 `index.html`을 더블클릭하면 끝입니다. 인터넷·서버·파이썬 모두 불필요.

브라우저에서 바로 열어보려면: <https://kepcokn5701.github.io/integrity/>

**B. Streamlit**

```bash
python -m streamlit run app.py
# → http://localhost:8502
```

## 사례 데이터 수정법

`cases.json`의 `cases` 배열에 항목을 추가하면 됩니다. 코드 수정·재배포 불필요
(Streamlit 캐시 때문에 파일 수정 후 앱 재시작 또는 브라우저에서 `C` → Clear cache).

```json
{
  "id": "GIFT-008",              // 카테고리키-일련번호, 중복 불가
  "category": "GIFT",            // categories 배열의 key 중 하나
  "sub": "선물",                  // 카테고리 안의 소분류 (자유롭게 신설 가능)
  "question": "…",               // 사용자가 물어볼 법한 문장 그대로
  "keywords": ["…"],             // 검색 보정용. 구어체·줄임말·금액을 넣을 것
  "verdict": "조건부 허용",        // 허용 / 조건부 허용 / 사전 신고·신청 / 금지
  "answer": "…",                 // 2~4문장. 결론 → 예외 → 실무 행동
  "basis": "청탁금지법 제8조 …",    // 근거. 필수 — 없으면 등록 금지
  "related": ["GIFT-002"],       // 존재하는 id만
  "updated": "2026-09-07"
}
```

`verdict`는 카드 상단 배지(🟢🟡🔵🔴)로 표시되므로 위 4개 값만 사용하세요.
수정 후 **`python build_html.py`를 다시 실행**해야 HTML에 반영됩니다.
정합성은 아래로 확인할 수 있습니다.

```bash
python -c "
import json
d=json.load(open('cases.json',encoding='utf-8'))
ids={c['id'] for c in d['cases']}; keys={c['key'] for c in d['categories']}
assert len(ids)==len(d['cases'])
for c in d['cases']:
    assert c['category'] in keys and c['basis'] and c['verdict']
    assert all(r in ids for r in c.get('related',[]))
print('OK', len(ids))
"
```

## 폐쇄망 배포 (B. Streamlit 기준)

A(단일 HTML)는 파일 하나를 공유 폴더나 사내 웹서버에 올리기만 하면 되므로
아래 절차가 필요 없습니다.

### 방법 A. 컨테이너 (권장)

인터넷 되는 PC에서 이미지를 만들어 통째로 반입합니다. `docker`를 `podman`으로
그대로 바꿔도 동일하게 동작합니다.

```bash
# ① 인터넷 PC
docker build -t integrity-bot:latest .
docker save integrity-bot:latest -o integrity-bot.tar

# ② 반입 후 사내 서버
docker load -i integrity-bot.tar
docker run -d --name integrity-bot -p 8502:8502 --restart unless-stopped \
  integrity-bot:latest
```

접속: `http://<서버IP>:8502`

사례만 수정할 때 이미지를 다시 만들기 번거로우면 파일을 마운트하세요.

```bash
docker run -d --name integrity-bot -p 8502:8502 \
  -v /srv/integrity/cases.json:/app/cases.json:ro \
  integrity-bot:latest
```

### 방법 B. wheels 반입

```bash
# ① 인터넷 PC — 대상 서버와 같은 OS/파이썬 버전으로 받을 것
pip download -r requirements.txt -d wheels

# ② 반입 후 사내 서버
./run_offline.sh
```

## 도입 전 반드시 할 일

1. **감사실 검토** — `cases.json`은 법령·행동강령 기준으로 작성한 초안입니다.
   기관 사규(수의계약 제한 범위, 겸직 허가 절차, 신고 창구 등)에 맞게 수정해야 합니다.
2. **가액 기준 확인** — 음식물·선물·경조사비 한도는 청탁금지법 시행령 개정에 따라
   바뀝니다. 현행 기준을 대조하세요. (`meta.amount_notice` 참고)
3. **감사실 연락처 입력** — `build_html.py`와 `app.py`의 `AUDIT_CONTACT` 딕셔너리.
4. **명칭 확정** — `build_html.py` / `app.py` 상단의 `APP_NAME`, `APP_SUBTITLE`.

## 설계 메모

- **LLM 자유 생성을 쓰지 않습니다.** 청렴 상담에서 모델이 "괜찮습니다"라고 답하면
  그건 기관 명의의 유권해석이 됩니다. 모든 답변은 등록된 사례와 근거 조문만
  출력하고, 검색 실패 시 감사실 문의로 유도합니다.
- 사례가 수백 건 이하이므로 벡터DB·임베딩 서버는 쓰지 않았습니다. 사례가 1,000건을
  넘거나 규정 원문 전체를 검색해야 하는 시점에 RAG 도입을 검토하면 됩니다.
- LLM을 붙인다면 **답변 생성이 아니라 질의 재작성/사례 요약** 용도로 한정하고,
  기존 사내 llama.cpp(OpenAI 호환) 엔드포인트를 재사용하는 것을 권장합니다.
- 사내 포털에 위젯(iframe) 형태로 심어야 하는 단계가 오면 FastAPI + 정적 HTML로
  이식하는 것이 맞습니다. 검색 로직(`app.py`의 `_grams`/`search`)은 그대로 옮겨집니다.
