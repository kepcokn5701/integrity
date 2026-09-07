# ==============================================================
#  청렴 나침반 — 인터랙티브 청렴 사례집
#  cases.json → 단일 HTML 파일 생성기
#  실행법: python build_html.py
#  결과물: 청렴나침반.html  (의존성 0 · 더블클릭 실행 · 외부 통신 없음)
# ==============================================================

import io
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "cases.json")
OUT_PATH = os.path.join(BASE_DIR, "청렴나침반.html")

APP_NAME = "청렴 나침반"
APP_SUBTITLE = "인터랙티브 청렴 사례집"

AUDIT_CONTACT = {
    "부서": "감사실 청렴윤리부",
    "전화": "내선 0000",
    "메일": "integrity@example.co.kr",
    "신고": "사내포털 &gt; 청렴신고센터",
}

# 첫 화면 하단에 노출할 자주 묻는 질문 (cases.json의 id)
FAQ_IDS = ["GIFT-001", "GIFT-002", "PUBL-002", "CONF-001"]


TEMPLATE = r"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>청렴 나침반 — 인터랙티브 청렴 사례집</title>
<style>
  * { box-sizing: border-box; }
  body {
    margin: 0; padding: 24px 16px;
    background: #eef2f9;
    font-family: "Malgun Gothic", "맑은 고딕", -apple-system, "Segoe UI", sans-serif;
    color: #1a2233; display: flex; justify-content: center;
  }
  .app {
    width: 100%; max-width: 600px; height: calc(100vh - 48px); min-height: 560px;
    background: linear-gradient(180deg, #f4f8ff 0%, #ffffff 42%);
    border-radius: 18px; box-shadow: 0 6px 32px rgba(30,50,90,.14);
    display: flex; flex-direction: column; overflow: hidden;
  }

  /* ── 헤더 ── */
  header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 16px 20px; background: #f4f8ff; border-bottom: 1px solid #e3eaf6;
    flex-shrink: 0;
  }
  header h1 { margin: 0; font-size: 16px; font-weight: 700; letter-spacing: -.3px; }
  header h1 .sub { display: block; font-size: 11px; font-weight: 500; color: #8b97ac; margin-top: 3px; letter-spacing: 0; }
  header .acts { display: flex; gap: 6px; }
  header button {
    width: 30px; height: 30px; border: 0; border-radius: 8px; cursor: pointer;
    background: transparent; color: #5a6b8a; font-size: 15px; line-height: 1;
  }
  header button:hover { background: #e5edfb; }

  /* ── 대화 영역 ── */
  .stream { flex: 1; overflow-y: auto; padding: 20px 18px 8px; scroll-behavior: smooth; }
  .msg { margin-bottom: 18px; display: flex; flex-direction: column; }
  .msg.bot { align-items: flex-start; }
  .msg.user { align-items: flex-end; }
  .who { display: flex; align-items: center; gap: 7px; margin-bottom: 6px; }
  .avatar {
    width: 26px; height: 26px; border-radius: 50%; flex-shrink: 0;
    background: linear-gradient(135deg,#4a7fe0,#7aa5f0);
    display: flex; align-items: center; justify-content: center; font-size: 13px;
  }
  .who span { font-size: 12px; color: #7a879e; }
  .bubble {
    max-width: 88%; padding: 12px 15px; border-radius: 4px 14px 14px 14px;
    background: #fff; border: 1px solid #e3eaf6; font-size: 14px; line-height: 1.7;
    box-shadow: 0 1px 3px rgba(30,50,90,.05); white-space: pre-line;
  }
  .msg.user .bubble {
    background: #2f6fd0; color: #fff; border: 0;
    border-radius: 14px 4px 14px 14px; white-space: normal;
  }
  .time { font-size: 11px; color: #a2adc0; margin-top: 5px; }

  /* ── 카드 그리드 ── */
  .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 9px; margin-top: 10px; width: 100%; }
  .card {
    background: #fff; border: 1px solid #e3eaf6; border-radius: 12px;
    padding: 14px 8px; text-align: center; cursor: pointer;
    transition: .13s; box-shadow: 0 1px 3px rgba(30,50,90,.05);
  }
  .card:hover { border-color: #2f6fd0; transform: translateY(-2px); box-shadow: 0 5px 14px rgba(47,111,208,.16); }
  .card .ic { font-size: 22px; display: block; margin-bottom: 7px; }
  .card .nm { font-size: 13px; font-weight: 600; }
  .card .ds { font-size: 11px; color: #8b97ac; margin-top: 3px; line-height: 1.4; }

  /* ── 목록형 버튼 ── */
  .list { display: flex; flex-direction: column; gap: 7px; margin-top: 10px; width: 100%; }
  .item {
    background: #fff; border: 1px solid #e3eaf6; border-radius: 10px;
    padding: 11px 14px; cursor: pointer; font-size: 13.5px; line-height: 1.5;
    display: flex; align-items: center; gap: 9px; text-align: left; transition: .13s;
  }
  .item:hover { border-color: #2f6fd0; background: #f8fbff; }
  .item .sc { margin-left: auto; font-size: 11px; color: #a2adc0; flex-shrink: 0; }
  .subhead { font-size: 12px; font-weight: 700; color: #6b7a94; margin: 12px 0 -2px 2px; }

  /* ── 답변 카드 ── */
  .answer {
    background: #fff; border: 1px solid #e3eaf6; border-radius: 4px 14px 14px 14px;
    padding: 16px 17px; max-width: 100%; box-shadow: 0 1px 3px rgba(30,50,90,.05);
  }
  .path { font-size: 11px; color: #a2adc0; margin-bottom: 9px; }
  .badge {
    display: inline-block; padding: 4px 11px; border-radius: 999px;
    font-size: 12px; font-weight: 700; margin-bottom: 10px;
  }
  .q { font-size: 15px; font-weight: 700; margin-bottom: 9px; line-height: 1.5; }
  .a { font-size: 14px; line-height: 1.8; color: #2b3648; }
  .basis {
    background: #f6f8fc; border-left: 3px solid #c3cddf; border-radius: 0 8px 8px 0;
    padding: 10px 13px; font-size: 12.5px; color: #55637d; margin-top: 13px; line-height: 1.6;
  }
  .disc {
    margin-top: 12px; padding: 10px 13px; background: #fffaf0; border: 1px solid #f2e2c4;
    border-radius: 8px; font-size: 12px; color: #85652a; line-height: 1.6;
  }
  .chips { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 12px; }
  .chip {
    border: 1px solid #cfdcf2; background: #f4f8ff; color: #2f6fd0;
    border-radius: 999px; padding: 6px 13px; font-size: 12.5px; cursor: pointer; transition: .13s;
  }
  .chip:hover { background: #2f6fd0; color: #fff; border-color: #2f6fd0; }

  /* ── 입력창 ── */
  .composer {
    display: flex; gap: 8px; padding: 12px 16px; border-top: 1px solid #e3eaf6;
    background: #fff; flex-shrink: 0;
  }
  .composer input {
    flex: 1; border: 1px solid #dbe3f0; border-radius: 999px; padding: 11px 17px;
    font-size: 14px; outline: none; font-family: inherit;
  }
  .composer input:focus { border-color: #2f6fd0; }
  .composer button {
    border: 0; border-radius: 999px; background: #2f6fd0; color: #fff;
    padding: 0 20px; font-size: 14px; font-weight: 600; cursor: pointer; font-family: inherit;
  }
  .composer button:hover { background: #245bb0; }
  .foot { padding: 9px 16px 12px; font-size: 10.5px; color: #a2adc0; line-height: 1.55; background: #fff; flex-shrink: 0; }

  .stream::-webkit-scrollbar { width: 7px; }
  .stream::-webkit-scrollbar-thumb { background: #cdd7e8; border-radius: 99px; }

  @media (max-width: 480px) {
    body { padding: 0; }
    .app { height: 100vh; border-radius: 0; }
    .grid { grid-template-columns: repeat(2, 1fr); }
  }
</style>
</head>
<body>
<div class="app">
  <header>
    <h1>🧭 <!--__NAME__--><span class="sub"><!--__SUBTITLE__--></span></h1>
    <div class="acts">
      <button id="btn-home" title="처음으로">⌂</button>
      <button id="btn-info" title="안내">ⓘ</button>
    </div>
  </header>

  <div class="stream" id="stream"></div>

  <div class="composer">
    <input id="q" type="text" placeholder="사례 검색 — 예) 명절 선물이 왔어요" autocomplete="off">
    <button id="send">전송</button>
  </div>
  <div class="foot" id="foot"></div>
</div>

<script>
const DATA = /*__DATA__*/;
const CONTACT = /*__CONTACT__*/;
const FAQ = /*__FAQ__*/;

const CASES = DATA.cases;
const CATS  = DATA.categories;
const BY_ID = {}; CASES.forEach(c => BY_ID[c.id] = c);
const CAT_NAME = {}; CATS.forEach(c => CAT_NAME[c.key] = c.name);

const VERDICT = {
  "허용":          ["🟢", "#0f7b3f", "#e6f5ec"],
  "조건부 허용":    ["🟡", "#8a6100", "#fdf3d8"],
  "사전 신고/신청": ["🔵", "#12508f", "#e4eefb"],
  "금지":          ["🔴", "#b3261e", "#fceceb"]
};

/* ───────── 검색: 문자 n-gram TF-IDF (외부 라이브러리 없음) ─────────
   2-gram은 '여비'·'겸직' 같은 짧은 단어를, 3-gram은 긴 문장의 변별력을 담당.
   한국어 조사·어미 변형과 오타에 강하도록 형태소 분석 대신 문자 단위로 처리. */
const NGRAMS = [2, 3];

function norm(t) {
  return (t || "").toLowerCase().replace(/[^0-9a-z가-힣]/g, "");
}
function grams(t) {
  const s = norm(t), out = [];
  for (const n of NGRAMS) {
    if (s.length < n) { if (s) out.push(s); }
    else for (let i = 0; i <= s.length - n; i++) out.push(s.slice(i, i + n));
  }
  return out;
}
function docText(c) {
  return [c.question, c.question, c.question,
          c.keywords.join(" "), c.keywords.join(" "), c.keywords.join(" "),
          c.sub, c.sub, CAT_NAME[c.category], c.answer, c.verdict].join(" ");
}

const IDF = {}, VECS = {};
(function buildIndex() {
  const df = {}, tfs = {};
  for (const c of CASES) {
    const tf = {};
    for (const g of grams(docText(c))) tf[g] = (tf[g] || 0) + 1;
    tfs[c.id] = tf;
    for (const g in tf) df[g] = (df[g] || 0) + 1;
  }
  const n = CASES.length;
  for (const g in df) IDF[g] = Math.log((n + 1) / (df[g] + 1)) + 1;
  for (const id in tfs) {
    const w = {};
    for (const g in tfs[id]) w[g] = (1 + Math.log(tfs[id][g])) * IDF[g];
    let sq = 0; for (const g in w) sq += w[g] * w[g];
    const nr = Math.sqrt(sq) || 1;
    for (const g in w) w[g] /= nr;
    VECS[id] = w;
  }
})();

function search(query, topK) {
  const qtf = {};
  for (const g of grams(query)) qtf[g] = (qtf[g] || 0) + 1;
  if (!Object.keys(qtf).length) return [];
  const qw = {};
  for (const g in qtf) qw[g] = (1 + Math.log(qtf[g])) * (IDF[g] || 1);
  let sq = 0; for (const g in qw) sq += qw[g] * qw[g];
  const nr = Math.sqrt(sq) || 1;
  for (const g in qw) qw[g] /= nr;

  const nq = norm(query), out = [];
  for (const c of CASES) {
    const v = VECS[c.id];
    let s = 0;
    for (const g in qw) if (v[g]) s += qw[g] * v[g];
    // 등록 키워드가 질문에 그대로 들어있으면 가산 (짧은 질의 보정)
    for (const k of c.keywords) {
      const nk = norm(k);
      if (nk && nq.indexOf(nk) !== -1) s += nk.length >= 2 ? 0.08 : 0.05;
    }
    if (s > 0.04) out.push([s, c]);
  }
  out.sort((a, b) => b[0] - a[0]);
  return out.slice(0, topK || 5);
}

/* ───────── 화면 ───────── */
const stream = document.getElementById("stream");
const esc = s => String(s).replace(/[&<>"]/g, m => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[m]));

function now() {
  const d = new Date(), h = d.getHours();
  const ap = h < 12 ? "오전" : "오후";
  const hh = h % 12 === 0 ? 12 : h % 12;
  return ap + " " + hh + ":" + String(d.getMinutes()).padStart(2, "0");
}
function scrollDown() { stream.scrollTop = stream.scrollHeight; }

function addUser(text) {
  const el = document.createElement("div");
  el.className = "msg user";
  el.innerHTML = '<div class="bubble">' + esc(text) + '</div><div class="time">' + now() + '</div>';
  stream.appendChild(el); scrollDown();
}

// body는 신뢰된 내부 데이터로 만든 HTML이라 그대로 삽입한다.
function addBot(body) {
  const el = document.createElement("div");
  el.className = "msg bot";
  el.innerHTML =
    '<div class="who"><div class="avatar">🧭</div><span><!--__NAME__--></span></div>' +
    body + '<div class="time">' + now() + '</div>';
  stream.appendChild(el); scrollDown();
  return el;
}

function catGrid() {
  return '<div class="grid">' + CATS.map(c =>
    '<div class="card" data-cat="' + c.key + '">' +
      '<span class="ic">' + c.icon + '</span>' +
      '<div class="nm">' + esc(c.name) + '</div>' +
      '<div class="ds">' + esc(c.desc) + '</div>' +
    '</div>').join("") + '</div>';
}

function caseItem(c, opts) {
  opts = opts || {};
  const ic = (VERDICT[c.verdict] || ["⚪"])[0];
  const cat = opts.showCat ? '[' + CAT_NAME[c.category] + '] ' : '';
  const sc = opts.score != null
    ? '<span class="sc">' + Math.round(Math.min(opts.score, 1) * 100) + '%</span>' : '';
  return '<div class="item" data-case="' + c.id + '"><span>' + ic + '</span>' +
         '<span>' + esc(cat + c.question) + '</span>' + sc + '</div>';
}

function greet() {
  stream.innerHTML = "";
  addBot('<div class="bubble">안녕하세요.\n청렴·행동강령 <b>사례집</b>을 대화하듯 찾아보는 도구입니다.\n\n' +
         '등록된 사례 ' + CASES.length + '건에서 찾아드립니다.\n' +
         '아래 항목을 선택하시거나, 상황을 그대로 입력해 검색해 보세요.</div>' +
         catGrid() +
         '<div class="subhead">자주 묻는 질문</div>' +
         '<div class="list">' + FAQ.filter(id => BY_ID[id]).map(id => caseItem(BY_ID[id])).join("") + '</div>');
}

function showCat(key) {
  const cat = CATS.find(c => c.key === key);
  addUser(cat.name);
  const list = CASES.filter(c => c.category === key);
  const subs = [];
  list.forEach(c => { if (subs.indexOf(c.sub) === -1) subs.push(c.sub); });
  const body = subs.map(s =>
    '<div class="subhead">' + esc(s) + '</div><div class="list">' +
    list.filter(c => c.sub === s).map(c => caseItem(c)).join("") + '</div>').join("");
  addBot('<div class="bubble">「' + esc(cat.name) + '」 관련 사례 ' + list.length +
         '건입니다. 해당하는 상황을 선택해 주세요.</div>' + body);
}

function showCase(id, skipUser) {
  const c = BY_ID[id];
  if (!skipUser) addUser(c.question);
  const v = VERDICT[c.verdict] || ["⚪", "#444", "#eee"];
  const rel = (c.related || []).filter(r => BY_ID[r]);
  const body =
    '<div class="answer">' +
      '<div class="path">' + esc(CAT_NAME[c.category] + " › " + c.sub) + ' · ' + c.id + '</div>' +
      '<span class="badge" style="color:' + v[1] + ';background:' + v[2] + '">' + v[0] + ' ' + esc(c.verdict) + '</span>' +
      '<div class="q">' + esc(c.question) + '</div>' +
      '<div class="a">' + esc(c.answer) + '</div>' +
      '<div class="basis">📖 <b>근거</b> · ' + esc(c.basis) + '</div>' +
      '<div class="disc">본 답변은 일반적인 기준 안내이며 <b>유권해석이 아닙니다.</b> ' +
        '구체적 사실관계에 따라 판단이 달라질 수 있으므로, 실제 결정 전 감사실에 확인하세요.</div>' +
      (rel.length ? '<div class="subhead">함께 보면 좋은 사례</div><div class="list">' +
        rel.map(r => caseItem(BY_ID[r], {showCat: true})).join("") + '</div>' : "") +
      '<div class="chips">' +
        '<div class="chip" data-act="contact">📮 감사실 문의</div>' +
        '<div class="chip" data-act="home">↩ 처음으로</div>' +
      '</div>' +
    '</div>';
  addBot(body);
}

function doSearch(text) {
  addUser(text);
  const hits = search(text, 5);
  if (!hits.length) {
    addBot('<div class="bubble">사례집에서 관련 내용을 찾지 못했습니다.\n' +
           '다른 표현으로 다시 검색하시거나, 아래 항목에서 찾아보세요.\n\n' +
           '판단이 어려운 사안은 감사실에 직접 문의하시는 것이 가장 정확합니다.</div>' +
           catGrid() +
           '<div class="chips"><div class="chip" data-act="contact">📮 감사실 문의</div></div>');
    return;
  }
  if (hits[0][0] > 0.3) {
    showCase(hits[0][1].id, true);
    const more = hits.slice(1, 4);
    if (more.length) {
      addBot('<div class="bubble">혹시 이런 내용을 찾으셨나요?</div><div class="list">' +
             more.map(h => caseItem(h[1], {showCat: true, score: h[0]})).join("") + '</div>');
    }
    return;
  }
  addBot('<div class="bubble">관련 있어 보이는 사례 ' + hits.length + '건입니다. 확인해 보세요.</div>' +
         '<div class="list">' + hits.map(h => caseItem(h[1], {showCat: true, score: h[0]})).join("") + '</div>');
}

function showContact() {
  addBot('<div class="bubble">감사실 연락처입니다.\n\n' +
    Object.keys(CONTACT).map(k => "· " + k + " : " + CONTACT[k]).join("\n") +
    '\n\n신고자의 신분은 비밀로 보장되며, 신고를 이유로 한 어떠한 불이익도 금지됩니다.</div>');
}

/* ───────── 이벤트 ───────── */
stream.addEventListener("click", e => {
  const card = e.target.closest("[data-cat]");
  if (card) return showCat(card.dataset.cat);
  const item = e.target.closest("[data-case]");
  if (item) return showCase(item.dataset.case);
  const chip = e.target.closest("[data-act]");
  if (chip) {
    if (chip.dataset.act === "contact") return showContact();
    if (chip.dataset.act === "home") return greet();
  }
});

const input = document.getElementById("q");
function submit() {
  const t = input.value.trim();
  if (!t) return;
  input.value = "";
  doSearch(t);
}
document.getElementById("send").addEventListener("click", submit);
input.addEventListener("keydown", e => { if (e.key === "Enter") submit(); });
document.getElementById("btn-home").addEventListener("click", greet);
document.getElementById("btn-info").addEventListener("click", () => {
  addBot('<div class="bubble">「<!--__NAME__-->」은 기존 청렴 챗봇과 <b>별개로</b>, ' +
    '청렴 <b>사례집</b>을 대화하듯 탐색하는 도구입니다.\n' +
    '상담을 대신하는 것이 아니라, 40페이지 사례집에서 필요한 한 건을 3초 만에 찾아주는 것이 목적입니다.\n\n' +
    '· 등록 사례 ' + CASES.length + '건 (최종 갱신 ' + DATA.meta.updated + ')\n' +
    '· 외부 통신 없이 이 파일 안에서만 동작합니다.\n' +
    '· 등록된 사례와 근거 조문만 제시하며, AI가 답을 새로 만들어내지 않습니다.\n' +
    '· 본 버전은 시연용 <b>프로토타입</b>입니다.</div>');
});

document.getElementById("foot").innerHTML =
  "⚠️ " + esc(DATA.meta.notice) + "<br>" + esc(DATA.meta.amount_notice);

greet();
</script>
</body>
</html>
"""


def main():
    with io.open(DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)

    dump = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    html = (
        TEMPLATE.replace("/*__DATA__*/", dump(data))
        .replace("/*__CONTACT__*/", dump(AUDIT_CONTACT))
        .replace("/*__FAQ__*/", dump(FAQ_IDS))
        .replace("<!--__NAME__-->", APP_NAME)
        .replace("<!--__SUBTITLE__-->", APP_SUBTITLE)
    )

    with io.open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    size = os.path.getsize(OUT_PATH)
    print("생성 완료: %s (%.1f KB, 사례 %d건)" % (OUT_PATH, size / 1024.0, len(data["cases"])))


if __name__ == "__main__":
    main()
