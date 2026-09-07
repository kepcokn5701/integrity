# ==============================================================
#  청렴 나침반 — 인터랙티브 청렴 사례집 (프로토타입)  v0.1
#  실행법: python -m streamlit run app.py
#  외부 통신 없음 · 폐쇄망 단독 구동
# ==============================================================

import json
import math
import os
import re
from collections import Counter, defaultdict

import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "cases.json")

AUDIT_CONTACT = {
    "부서": "감사실 청렴윤리부",
    "전화": "내선 0000",
    "메일": "integrity@example.co.kr",
    "신고": "사내포털 > 청렴신고센터",
}

VERDICT_STYLE = {
    "허용": ("🟢", "#0f7b3f", "#e6f5ec"),
    "조건부 허용": ("🟡", "#8a6100", "#fdf3d8"),
    "사전 신고/신청": ("🔵", "#12508f", "#e4eefb"),
    "금지": ("🔴", "#b3261e", "#fceceb"),
}

APP_NAME = "청렴 나침반"
APP_SUBTITLE = "인터랙티브 청렴 사례집"

st.set_page_config(page_title="%s — %s" % (APP_NAME, APP_SUBTITLE), page_icon="🧭", layout="centered")


# ───────────────────────── 데이터 ─────────────────────────
@st.cache_data(show_spinner=False)
def load_data():
    with open(DATA_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    cases = raw["cases"]
    by_id = {c["id"]: c for c in cases}
    cats = raw["categories"]
    by_cat = defaultdict(list)
    for c in cases:
        by_cat[c["category"]].append(c)
    return raw["meta"], cats, cases, by_id, dict(by_cat)


# ─────────────────── 검색 (문자 n-gram TF-IDF) ───────────────────
# 폐쇄망 반입 부담을 줄이려고 외부 검색 라이브러리 없이 순수 파이썬으로 구현.
# 한국어 조사·어미 변형과 오타에 강하도록 형태소 분석 대신 문자 n-gram을 씀.
# 2-gram은 '여비'·'겸직' 같은 짧은 단어를, 3-gram은 긴 문장의 변별력을 담당.
NGRAMS = (2, 3)


def _norm(text):
    return re.sub(r"[^0-9a-z가-힣]", "", text.lower())


def _grams(text):
    s = _norm(text)
    out = []
    for n in NGRAMS:
        if len(s) < n:
            if s:
                out.append(s)
        else:
            out.extend(s[i : i + n] for i in range(len(s) - n + 1))
    return out


def _doc_text(case, cat_name):
    # 질문·키워드에 가중치를 주려고 단순 반복
    return " ".join(
        [case["question"]] * 3
        + case["keywords"] * 3
        + [case["sub"]] * 2
        + [cat_name, case["answer"], case["verdict"]]
    )


@st.cache_data(show_spinner=False)
def build_index(_cases, _cats):
    cat_name = {c["key"]: c["name"] for c in _cats}
    vecs, df = {}, Counter()
    for c in _cases:
        tf = Counter(_grams(_doc_text(c, cat_name[c["category"]])))
        vecs[c["id"]] = tf
        df.update(tf.keys())
    n = len(_cases)
    idf = {g: math.log((n + 1) / (v + 1)) + 1 for g, v in df.items()}

    index = {}
    for cid, tf in vecs.items():
        w = {g: (1 + math.log(f)) * idf[g] for g, f in tf.items()}
        norm = math.sqrt(sum(v * v for v in w.values())) or 1.0
        index[cid] = {g: v / norm for g, v in w.items()}
    return index, idf


def search(query, cases, index, idf, top_k=6):
    q_tf = Counter(_grams(query))
    if not q_tf:
        return []
    q_w = {g: (1 + math.log(f)) * idf.get(g, 1.0) for g, f in q_tf.items()}
    q_norm = math.sqrt(sum(v * v for v in q_w.values())) or 1.0
    q_w = {g: v / q_norm for g, v in q_w.items()}

    nq = _norm(query)
    scored = []
    for c in cases:
        vec = index[c["id"]]
        score = sum(w * vec.get(g, 0.0) for g, w in q_w.items())
        # 등록 키워드가 질문에 그대로 들어있으면 가산 (짧은 질의 보정)
        # '밥' 같은 1글자 키워드도 인정하되 가중치는 낮춘다.
        for k in c["keywords"]:
            nk = _norm(k)
            if nk and nk in nq:
                score += 0.08 if len(nk) >= 2 else 0.05
        if score > 0.04:
            scored.append((score, c))
    scored.sort(key=lambda x: -x[0])
    return scored[:top_k]


# ───────────────────────── 상태 ─────────────────────────
def go(view, **kw):
    st.session_state.view = view
    st.session_state.update(kw)


def clear_query():
    # 위젯 key를 바꿔 새 위젯으로 만들면 입력값이 확실히 비워진다.
    # (이미 렌더된 위젯의 session_state를 직접 수정하면 예외가 발생)
    st.session_state.qnonce += 1
    st.session_state.query = ""


if "view" not in st.session_state:
    st.session_state.view = "home"
    st.session_state.cat = None
    st.session_state.case_id = None
    st.session_state.query = ""
    st.session_state.qnonce = 0

meta, CATS, CASES, BY_ID, BY_CAT = load_data()
INDEX, IDF = build_index(CASES, CATS)
CAT_NAME = {c["key"]: c["name"] for c in CATS}


# ───────────────────────── 스타일 ─────────────────────────
st.markdown(
    """
<style>
  .block-container {padding-top: 2rem; max-width: 760px;}
  .hero {background: linear-gradient(135deg,#eef4ff 0%,#f7faff 100%);
         border-radius: 16px; padding: 22px 24px; margin-bottom: 18px;}
  .hero h2 {margin: 0 0 6px 0; font-size: 22px;}
  .hero h2 .sub {font-size: 13px; font-weight: 500; color: #7a879e; margin-left: 6px;}
  .hero p {margin: 0; color: #4a5568; font-size: 14px; line-height: 1.6;}
  .badge {display:inline-block; padding:4px 12px; border-radius:999px;
          font-size:13px; font-weight:600; margin-bottom:10px;}
  .basis {background:#f6f7f9; border-left:3px solid #c4c9d4; padding:10px 14px;
          border-radius:0 8px 8px 0; font-size:13px; color:#4a5568; margin-top:12px;}
  .caseq {font-size:17px; font-weight:600; margin:2px 0 10px 0;}
  .ans {font-size:15px; line-height:1.75;}
  .hitline {font-size:12px; color:#8892a4; margin:-6px 0 2px 2px;}
  div[data-testid="stButton"] button {height:100%; min-height:52px; white-space:normal;
          text-align:left; line-height:1.45;}
</style>
""",
    unsafe_allow_html=True,
)


def render_case_button(case, key_prefix, show_cat=False):
    icon = VERDICT_STYLE.get(case["verdict"], ("⚪",))[0]
    prefix = "[%s] " % CAT_NAME[case["category"]] if show_cat else ""
    label = "%s %s%s" % (icon, prefix, case["question"])
    if st.button(label, key="%s_%s" % (key_prefix, case["id"]), use_container_width=True):
        go("case", case_id=case["id"])
        st.rerun()


# ───────────────────────── 상단 검색 ─────────────────────────
st.markdown(
    """
<div class="hero">
  <h2>🧭 %s <span class="sub">%s</span></h2>
  <p>청렴·행동강령 <b>사례집</b>을 대화하듯 찾아보는 도구입니다.
  등록된 사례 %d건에서 찾아드립니다.<br>
  아래 항목을 선택하시거나, 상황을 그대로 입력해 검색해 보세요.</p>
</div>
"""
    % (APP_NAME, APP_SUBTITLE, len(CASES)),
    unsafe_allow_html=True,
)

q = st.text_input(
    "검색",
    placeholder="사례 검색 — 예) 거래처에서 명절 선물이 왔어요 / 법인카드 주말 사용",
    label_visibility="collapsed",
    key="q%d" % st.session_state.qnonce,
)
if q != st.session_state.query:
    st.session_state.query = q
    go("search" if q.strip() else "home")
    st.rerun()

if st.session_state.view != "home":
    if st.button("← 처음으로", key="home_btn"):
        clear_query()
        go("home", cat=None, case_id=None)
        st.rerun()

st.divider()


# ───────────────────────── 화면 ─────────────────────────
view = st.session_state.view

if view == "home":
    cols = st.columns(3)
    for i, cat in enumerate(CATS):
        with cols[i % 3]:
            label = "%s **%s**\n\n%s" % (cat["icon"], cat["name"], cat["desc"])
            if st.button(label, key="cat_%s" % cat["key"], use_container_width=True):
                go("cat", cat=cat["key"])
                st.rerun()
    st.caption("등록된 사례 %d건 · 최종 갱신 %s" % (len(CASES), meta["updated"]))

elif view == "cat":
    cat = next(c for c in CATS if c["key"] == st.session_state.cat)
    st.subheader("%s %s" % (cat["icon"], cat["name"]))
    for sub in dict.fromkeys(c["sub"] for c in BY_CAT[cat["key"]]):
        st.markdown("**%s**" % sub)
        for case in [c for c in BY_CAT[cat["key"]] if c["sub"] == sub]:
            render_case_button(case, "c")
        st.write("")

elif view == "search":
    results = search(st.session_state.query, CASES, INDEX, IDF)
    if not results:
        st.warning(
            "사례집에서 관련 내용을 찾지 못했습니다. 다른 표현으로 검색하시거나, "
            "아래 항목에서 찾아보세요.\n\n"
            "판단이 어려운 사안은 **감사실에 직접 문의**하시는 것이 가장 정확합니다."
        )
        cols = st.columns(3)
        for i, cat in enumerate(CATS):
            with cols[i % 3]:
                if st.button("%s %s" % (cat["icon"], cat["name"]),
                             key="scat_%s" % cat["key"], use_container_width=True):
                    clear_query()
                    go("cat", cat=cat["key"])
                    st.rerun()
    else:
        st.markdown("**‘%s’** 관련 사례 %d건을 찾았습니다." % (st.session_state.query, len(results)))
        for score, case in results:
            st.markdown('<div class="hitline">유사도 %d%%</div>' % round(min(score, 1.0) * 100),
                        unsafe_allow_html=True)
            render_case_button(case, "s", show_cat=True)

elif view == "case":
    case = BY_ID[st.session_state.case_id]
    icon, fg, bg = VERDICT_STYLE.get(case["verdict"], ("⚪", "#444", "#eee"))

    st.caption("%s › %s · %s" % (CAT_NAME[case["category"]], case["sub"], case["id"]))
    st.markdown(
        '<span class="badge" style="color:%s;background:%s;">%s %s</span>'
        % (fg, bg, icon, case["verdict"]),
        unsafe_allow_html=True,
    )
    st.markdown('<div class="caseq">%s</div>' % case["question"], unsafe_allow_html=True)
    st.markdown('<div class="ans">%s</div>' % case["answer"], unsafe_allow_html=True)
    st.markdown('<div class="basis">📖 <b>근거</b> · %s</div>' % case["basis"], unsafe_allow_html=True)

    related = [BY_ID[r] for r in case.get("related", []) if r in BY_ID]
    if related:
        st.write("")
        st.markdown("**함께 보면 좋은 사례**")
        for rc in related:
            render_case_button(rc, "r", show_cat=True)

    st.write("")
    st.info(
        "본 답변은 일반적인 기준 안내이며 **유권해석이 아닙니다.** "
        "구체적 사실관계에 따라 판단이 달라질 수 있으므로, 실제 결정 전 감사실에 확인하세요."
    )
    with st.expander("📮 감사실에 직접 문의하기", expanded=False):
        for k, v in AUDIT_CONTACT.items():
            st.markdown("- **%s** : %s" % (k, v))


# ───────────────────────── 하단 고정 ─────────────────────────
st.divider()
c1, c2 = st.columns(2)
with c1:
    if st.button("📮 감사실 문의", use_container_width=True):
        go("case", case_id="SOLI-005")
        st.rerun()
with c2:
    if st.button("🛡️ 신고자 보호 안내", use_container_width=True):
        go("case", case_id="SOLI-005")
        st.rerun()
st.caption(
    "「%s」은 기존 청렴 챗봇과 별개로, 청렴 사례집을 대화하듯 탐색하는 도구입니다. "
    "등록된 사례와 근거 조문만 제시하며 AI가 답을 새로 만들어내지 않습니다." % APP_NAME
)
st.caption("⚠️ " + meta["notice"])
st.caption(meta["amount_notice"])
