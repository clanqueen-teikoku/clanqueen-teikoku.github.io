#!/usr/bin/env python3
"""CLAN QUEEN 秘密の帝国: data/timeline.json から docs/ に静的サイトを生成する。
（つくりは「Ado 非公式ワクワク秘密基地」~/ado-himitsukichi・「yamaファンのこっそり部屋」~/yama-kossori と同じ）

- data/timeline.json … 年表。tools/mk_data.py が data/core.json（手書きの節目）・公式 YouTube・公式サイトのライブ一覧から作る。
  {date: "YYYY" | "YYYY-MM" | "YYYY-MM-DD", cat, title, note, big, videos?, shows?}
  cat: wic（前身 WARS iN CLOSET）/ youtube / feat / release / live / tieup / media / award / milestone
  毎月の更新では、前の月のできごとを data/core.json に足して mk_data.py → build.py を走らせる。
- これからの予定 … ~/knowledge-os/oshi-events.js（毎週月曜に更新される推しイベント一覧）から artist が CLAN QUEEN の行を docs/upcoming.js に書き出す。
- 画像 … 公式素材の複製・転載はしない。置く画像は Gemini でつくったオリジナルのヘッダー（assets/header.jpg・2026-10-23。上書きしない）だけ。
  MV は data/mv.json（曲名→公式 YouTube の動画 ID）から YouTube のサムネイルを i.ytimg.com から直接表示し、動画にリンクする。
  CLAN QUEEN 公式チャンネル = UCfmt9Ux4KjlTZESqFwGG-Yw。feat. はそのアーティスト本人の公式チャンネルの動画だけ。
非公式のファンサイト。アフィリエイト・広告は入れない。歌詞の引用や公式素材は載せない。
"""
import html, json, os, re, shutil
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "docs")
NAME = "CLAN QUEEN 秘密の帝国"
ARTIST = "CLAN QUEEN"
SITE = "https://clanqueen-teikoku.github.io/"
GA = "G-EHWF25C1RB"  # ほかのサイトと共通の測定 ID（GA4 でホスト名 clanqueen-teikoku.github.io で絞る）
EVENTS_JS = os.path.expanduser("~/knowledge-os/oshi-events.js")
TODAY = date.today().isoformat()

CATS = {
    "youtube": ("YouTube", "#22a7a0"),
    "feat": ("客演・参加", "#8b5cf6"),
    "wic": ("WARS iN CLOSET", "#9f1239"),
    "release": ("リリース", "#2563eb"),
    "live": ("ライブ・ツアー", "#e11d48"),
    "tieup": ("タイアップ", "#ea580c"),
    "media": ("テレビ・ラジオ", "#0891b2"),
    "award": ("受賞・記録", "#ca8a04"),
    "milestone": ("できごと", "#475569"),
}
# 時代区分（トップのカードと時代ページ）
ERAS = [
    ("closet", "WARS iN CLOSET の部屋", "前身バンド WARS iN CLOSET の 6 曲と、CLAN QUEEN 始動の前夜", "0000", "2022-10-31", "wic:New Error!!"),
    ("hellfire", "ヘルファイアクラブ", "始動・初ライブから 1st アルバム『VeiL』と初ワンマンまで", "2022-11-01", "2024-04-30", "ヘルファイアクラブ"),
    ("toys", "TOYS と NEBULA", "『TOYS』初のワンマンツアーから『NEBULA』初の全国流通・タワレコメンまで", "2024-05-01", "2025-12-31", "ゲルニカ"),
    ("empire", "Secret Empire", "「Whitoxin」、歌舞伎町のフリーライブ『99』とメジャーデビュー、Zepp ツアー", "2026-01-01", "2026-08-31", "無花果"),
    ("ima", "いま、そしてこれから", "初のアニメタイアップ「WARNING!!」と東京ガーデンシアター、ホールツアーへ", "2026-09-01", "9999", "WARNING!!"),
]
CAT_PAGES = [("release", "リリース"), ("live", "ライブ・ツアー"), ("tieup", "タイアップ・テレビ")]

esc = html.escape
MV = json.load(open(os.path.join(ROOT, "data", "mv.json"), encoding="utf-8"))
MAGS = sorted(json.load(open(os.path.join(ROOT, "data", "magazines.json"), encoding="utf-8")), key=lambda e: e["date"])  # 公式 X・公式サイトで告知された雑誌・Web インタビュー
SETLISTS = json.load(open(os.path.join(ROOT, "data", "setlists.json"), encoding="utf-8"))  # setlist.fm から（ファン投稿）
SL_ID = {x["sfid"]: x for x in SETLISTS}
OFFICIAL = []  # 公式のセットリスト告知（見つかったら data/official_setlists.json に足す）
OFF_DATE = {d: o for o in OFFICIAL for d in o["dates"]}
SL_DATE = {}
for x in SETLISTS:
    SL_DATE.setdefault(x["date"], []).append(x)
T = sorted(json.load(open(os.path.join(ROOT, "data", "timeline.json"), encoding="utf-8")),
           key=lambda e: e["date"])


def expand_shows(T):
    """ツアー・複数日公演の "shows" を 1 公演 = 1 項目に展開する（どれだけ行動したかを日ごとに見せるため）。"""
    out = []
    for e in T:
        shows = e.get("shows")
        if not shows:
            out.append(e)
            continue
        m = re.search(r"『(.+)』", e["title"]) or re.search(r"「([^」]+)」", e["title"])
        name = m.group(1) if m else e["title"]
        n = len(shows)
        for i, x in enumerate(shows, 1):
            tag = "初日" if i == 1 else ("千秋楽" if i == n else "")
            info = f"{x['venue']}。全 {n} 公演の {i} 公演目" + (f"（{tag}）" if tag and n > 1 else "") + "。"
            if i == 1:
                e2 = dict(e)
                e2["note"] = (e.get("note", "") + " " if e.get("note") else "") + f"{x['place']}・{info}"
                e2.pop("shows", None)
                if x.get("videos"):
                    e2["videos"] = list(e.get("videos", [])) + x["videos"]
                out.append(e2)
            else:
                out.append({"date": x["date"], "cat": e["cat"], "title": f"『{name}』{x['place']} 公演", "note": info, "big": False, "show": True, "videos": x.get("videos", [])})
    return sorted(out, key=lambda e: e["date"])


T = expand_shows(T)


def year_stats(y):
    ev = [e for e in T if e["date"][:4] == y]
    c = lambda cats: sum(1 for e in ev if e["cat"] in cats)
    parts = [("ライブ", c({"live"}), "公演"), ("リリース", c({"release", "tieup"}), "件"), ("WARS iN CLOSET", c({"wic"}), "件"), ("YouTube", c({"youtube"}), "本"),
             ("客演", c({"feat"}), "曲"), ("テレビ・ラジオ", c({"media"}), "件")]
    return " ／ ".join(f"{a} {n} {u}" for a, n, u in parts if n)


def fmt(d):
    p = d.split("-")
    s = p[0] + "年"
    if len(p) > 1:
        s += str(int(p[1])) + "月"
    if len(p) > 2:
        s += str(int(p[2])) + "日"
    return s


def era_of(d):
    for e in ERAS:
        if e[3] <= d <= e[4] + "~":
            return e
    return ERAS[-1]


def thumb_url(vid, size="hqdefault"):
    return f"https://i.ytimg.com/vi/{vid}/{size}.jpg"


def watch(vid):
    return f"https://www.youtube.com/watch?v={vid}"


def nico_url(sm):
    return f"https://www.nicovideo.jp/watch/{sm}"


def link_of(m):
    """動画の飛び先と、サムネイル URL と、サービス名。YouTube を優先し、無ければニコニコ動画。"""
    if m.get("id"):
        return watch(m["id"]), thumb_url(m["id"]), "YouTube"
    return nico_url(m["nico"]), m["nico_thumb"], "ニコニコ動画"


def thumb(song, cls="pic"):
    m = MV.get(song)
    if not m:
        return f'<div class="{cls} ph"></div>'
    _, src, svc = link_of(m)
    return f'<img class="{cls}" src="{src}" alt="{esc(m["title"])} のサムネイル（{svc}）" loading="lazy">'


def songs_in(e):
    """年表の項目の「」から、MV がある曲名を拾う。"""
    out = []
    for q in re.findall(r"「([^」]+)」", e["title"] + " " + e.get("note", "")):
        for k in MV:
            if (k == q or (len(k) >= 3 and k in q)) and k not in out:
                out.append(k)
    return out


def where(m, svc):
    if m.get("kind") == "タイアップ":
        return f"{svc} で見る（タイアップ先: {esc(m['by'])}）"
    if m.get("by"):
        return f"{svc} で見る（{esc(m['by'])} 公式）"
    return f"{svc} で見る（CLAN QUEEN 公式チャンネル）"


def mv_card(k):
    m = MV[k]
    href, src, svc = link_of(m)
    if svc == "YouTube":
        src = thumb_url(m["id"], "mqdefault")
    nico = ""
    if m.get("id") and m.get("nico"):
        nico = f'<a class="nl" href="{nico_url(m["nico"])}" target="_blank" rel="noopener">ニコニコ動画でも見る →</a>'
    return (f'<div class="mvw"><a class="mv{" nc" if svc != "YouTube" else ""}" href="{href}" target="_blank" rel="noopener">'
            f'<span class="th"><img src="{src}" alt="" loading="lazy"><i>▶</i></span>'
            f'<span class="mt">{esc(m["title"])}<small>{where(m, svc)}</small></span></a>{nico}</div>')


TIEUP = {k: v for k, v in json.load(open(os.path.join(ROOT, "data", "tieup_videos.json"), encoding="utf-8")).items() if not k.startswith("_")}
for _song, _vs in TIEUP.items():
    for _v in _vs:
        MV[f"tieup:{_v['id']}"] = {"id": _v["id"], "title": _v["title"], "kind": "タイアップ", "by": _v["by"], "yt_date": _v["date"]}


def with_tieup_videos(e):
    """タイアップページ用: その曲のタイアップ先の公式動画を項目の動画に足す。"""
    songs = list(e.get("videos") or songs_in(e))
    extra = [f"tieup:{v['id']}" for s in songs for v in TIEUP.get(s, [])]
    if not extra:
        return e
    e2 = dict(e)
    e2["videos"] = songs + [k for k in extra if k not in songs]
    return e2


def x_embed(url):
    return (f'<div class="xpost"><blockquote class="twitter-tweet" data-lang="ja" data-dnt="true">'
            f'<a href="{url}">公式 X のポストを見る</a></blockquote></div>')


def setlist_body(songs):
    body, n, cur, start = "", 0, [], 1
    for x in songs:
        if x.get("sec"):
            if cur:
                body += f'<ol start="{start}">' + "".join(cur) + "</ol>"
            start, cur = n + 1, []
            body += f'<p class="sec">{esc(x["sec"])}</p>'
        else:
            n += 1
            small = f'<small>{esc(x["n"])}</small>' if x.get("n") else ""
            cur.append(f'<li>{esc(x["t"])}{small}</li>')
    if cur:
        body += f'<ol start="{start}">' + "".join(cur) + "</ol>"
    return f'<div class="slb">{body}</div>', n


def item(e, show_year=True):
    name, color = CATS.get(e["cat"], ("その他", "#64748b"))
    note = f'<p>{esc(e["note"])}</p>' if e.get("note") else ""
    auto = songs_in(e) if e["cat"] not in ("live", "media") else []  # ライブの公演名からは曲を拾わない（「us」などの誤マッチを防ぐ）
    note += "".join(mv_card(k) for k in (e.get("videos") or auto) if k in MV)
    sl = SL_ID.get(e.get("sfid")) or (SL_DATE[e["date"]][0] if e["cat"] == "live" and len(SL_DATE.get(e["date"], [])) == 1 else None)
    off = OFF_DATE.get(e["date"]) if e["cat"] == "live" else None
    if off:
        src = f'出典: <a href="{esc(off["x"])}" target="_blank" rel="noopener">公式 X</a>'
        if off.get("playlist"):
            src += f'・<a href="{esc(off["playlist"])}" target="_blank" rel="noopener">公式プレイリスト</a>'
        if len(off["dates"]) > 1:
            src += "（ツアー共通のセットリスト）"
        if off.get("note"):
            src += "。" + esc(off["note"])
        body, n = setlist_body(off["songs"])
        note += f'<details class="sl"><summary>セットリスト（公式・{n} 曲）</summary>{body}<p class="src">{src}</p></details>'
    if sl and sl.get("songs"):
        body, n = setlist_body(sl["songs"])
        lab = f"この日のファンの記録（setlist.fm・{n} 曲）" if off else f"セットリスト（{n} 曲）"
        note += (f'<details class="sl{" fan" if off else ""}"><summary>{lab}</summary>{body}'
                 f'<p class="src">出典: <a href="{esc(sl["url"])}" target="_blank" rel="noopener">setlist.fm</a>（ファンによる投稿をもとに曲名を日本語にしています。公式発表と違う場合があります）</p></details>')
    if e.get("x"):
        note += x_embed(e["x"])
    star = ' big' if e.get("big") else ''
    return (f'<li class="ev{star}"><div class="dt">{fmt(e["date"]) if show_year else fmt(e["date"])[5:] or fmt(e["date"])}</div>'
            f'<div class="bd"><span class="chip" style="--c:{color}">{name}</span>'
            f'<h3>{esc(e["title"])}</h3>{note}</div></li>')


def timeline(events, by_year=True):
    if not events:
        return '<p class="empty">まだ記録がありません。</p>'
    out, cur = [], None
    for e in events:
        y = e["date"][:4]
        if by_year and y != cur:
            if cur:
                out.append("</ol>")
            st = year_stats(y)
            out.append(f'<h2 class="yr" id="y{y}"><a href="{{R}}year/{y}.html">{y}年</a> <small class="ys">{len([x for x in T if x["date"][:4] == y])} のできごと{"（" + st + "）" if st else ""}</small></h2><ol class="tl">')
            cur = y
        out.append(item(e))
    out.append("</ol>")
    if not by_year:
        out.insert(0, '<ol class="tl">')
    return "\n".join(out)


YEARS = sorted({e["date"][:4] for e in T})

NAV = [("index.html", "帝国トップ"), ("timeline.html", "全部の年表"), ("wic.html", "WARS iN CLOSET"),
       ("release.html", "リリース"), ("live.html", "ライブ"), ("tieup.html", "タイアップ"), ("mv.html", "MV"),
       ("setlists.html", "セットリスト"), ("magazines.html", "雑誌インタビュー"), ("x.html", "公式Xまとめ"), ("schedule.html", "これからの予定"), ("about.html", "この帝国について")]

CSS = """
:root{--bg:#f6f2f2;--card:#fff;--ink:#22161a;--sub:#6b5a5f;--line:#eadfe1;--ac:#a3123a;--ac2:#c81e4a;--yl:#e8c37a;--hd:#140709}
@media (prefers-color-scheme:dark){:root{--bg:#0d0809;--card:#1a1113;--ink:#f2e9ea;--sub:#b8a7ab;--line:#342226;--ac:#ff7a96;--ac2:#ff5577;--hd:#070304}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:"Hiragino Sans","Noto Sans JP",sans-serif;line-height:1.8;font-size:16px}
a{color:var(--ac)}img{max-width:100%;display:block}
.top{background:var(--hd);color:#fff}.top .in{max-width:1180px;margin:auto;padding:12px 16px;display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.logo{color:#fff;text-decoration:none;font-weight:800;font-size:20px;letter-spacing:.02em}.logo span{color:var(--yl)}
.badge{font-size:11px;border:1px solid #fff6;border-radius:99px;padding:1px 8px;color:#fffc}
.gnav{background:var(--card);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:5}
.gnav ul{max-width:1180px;margin:auto;padding:0 8px;list-style:none;display:flex;overflow-x:auto;gap:2px}
.gnav a{display:block;padding:10px 12px;white-space:nowrap;text-decoration:none;color:var(--ink);font-size:14px;font-weight:600;border-bottom:3px solid transparent}
.gnav a.on,.gnav a:hover{border-color:var(--ac2);color:var(--ac2)}
.hero{max-width:1180px;margin:16px auto 0;padding:0 16px}.hero img,.hero .ph{width:100%;aspect-ratio:2.5/1;object-fit:cover;border-radius:14px}
.hero .hdr{width:100%;height:auto;aspect-ratio:auto;border-radius:14px;display:block;margin-bottom:10px}
.ph{background:linear-gradient(135deg,#140709,#8a1031 55%,#e8c37a)}
.layout{max-width:1180px;margin:20px auto;padding:0 16px;display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:24px}
@media(max-width:900px){.layout{grid-template-columns:1fr}}
main>section,.box{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px;margin-bottom:20px}
.crumb{font-size:13px;color:var(--sub);margin-bottom:8px}.crumb a{color:var(--sub)}
h1{font-size:26px;line-height:1.4;margin:0 0 8px}h2{font-size:20px;margin:0 0 12px}
.lead{color:var(--sub);margin:0}
.sec-t{display:flex;align-items:center;gap:8px}.sec-t:before{content:"";width:6px;height:22px;background:var(--ac2);border-radius:3px}
.eras{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:14px}
.era{display:block;text-decoration:none;color:inherit;border:1px solid var(--line);border-radius:12px;overflow:hidden;background:var(--bg);transition:transform .15s}
.era:hover{transform:translateY(-3px)}.pic{border-radius:10px;}.era .pic{border-radius:0;width:100%;aspect-ratio:16/10;object-fit:cover}
.era div.t{padding:10px 12px}.era b{display:block;font-size:16px}.era small{color:var(--sub);font-size:12.5px;line-height:1.5;display:block}
.era .n{font-size:12px;color:var(--ac2);font-weight:700}
.years{display:grid;grid-template-columns:repeat(auto-fill,minmax(96px,1fr));gap:8px}
.years a{display:block;text-align:center;padding:10px 4px;border-radius:10px;background:var(--bg);border:1px solid var(--line);text-decoration:none;color:var(--ink);font-weight:700}
.years a small{display:block;font-weight:400;color:var(--sub);font-size:12px}
.years a:hover{border-color:var(--ac)}
.yr{margin:24px 0 8px;font-size:22px}.yr a{color:var(--ink);text-decoration:none}.yr:first-child{margin-top:0}
.tl{list-style:none;margin:0;padding:0;border-left:3px solid var(--line);margin-left:6px}
.ev{position:relative;padding:4px 0 14px 18px;display:grid;grid-template-columns:120px 1fr;gap:10px}
.ev:before{content:"";position:absolute;left:-8px;top:12px;width:13px;height:13px;border-radius:50%;background:var(--card);border:3px solid var(--line)}
.ev.big:before{background:var(--yl);border-color:var(--ac2)}
.ev .dt{font-size:13.5px;color:var(--sub);font-weight:700;padding-top:2px}
.ev h3{margin:2px 0 0;font-size:16.5px;line-height:1.5}.ev.big h3{color:var(--ac2)}.ev p{margin:2px 0 0;font-size:14.5px;color:var(--sub)}
@media(max-width:560px){.ev{grid-template-columns:1fr;gap:0}}
.chip{display:inline-block;font-size:11.5px;font-weight:700;color:var(--c);border:1px solid var(--c);border-radius:99px;padding:0 8px;line-height:1.7}
.up{list-style:none;margin:0;padding:0}.up li{display:flex;gap:12px;padding:10px 0;border-bottom:1px dashed var(--line)}
.up li:last-child{border:0}.up .d{flex:0 0 74px;text-align:center;background:var(--bg);border-radius:10px;padding:4px;font-weight:800;line-height:1.3}
.up .d small{display:block;font-weight:400;font-size:11px;color:var(--sub)}.up .k{font-size:11.5px;color:var(--ac2);font-weight:700}
.side .box{padding:16px}.side h2{font-size:16px}.side ul{list-style:none;margin:0;padding:0}.side li a{display:block;padding:6px 4px;border-bottom:1px solid var(--line);text-decoration:none;color:var(--ink);font-size:14.5px}
.side li a:hover{color:var(--ac2)}.side .note{font-size:13px;color:var(--sub);margin:0}
.side .sticky{position:sticky;top:56px}
.notice{font-size:13.5px;background:var(--bg);border-left:4px solid var(--yl);padding:10px 12px;border-radius:6px;color:var(--sub)}
.pager{display:flex;justify-content:space-between;gap:10px;margin-top:10px;flex-wrap:wrap}
.pager a{padding:8px 14px;border:1px solid var(--line);border-radius:99px;text-decoration:none;background:var(--card)}
.empty{color:var(--sub)}
.sl{margin-top:8px}.sl summary{display:inline-block;cursor:pointer;list-style:none;font-size:13px;font-weight:700;padding:3px 14px;border-radius:99px;background:#000;color:#e8c37a;border:1px solid #e8c37a}
.sl summary::-webkit-details-marker{display:none}.sl.fan summary{color:#c9c9c9;border-color:#777;font-weight:600}.sl summary:hover{background:#1a1a1a}.sl[open] summary{margin-bottom:6px}
.sl .slb{padding:8px 12px;background:var(--bg);border:1px solid var(--line);border-radius:10px;max-width:520px}
.sl ol{margin:0;padding-left:24px;font-size:14px;line-height:1.75}.sl .sec{margin:6px 0 2px;font-weight:700;color:var(--ac2);font-size:13px}
.sl ol li small{color:var(--sub);font-size:12px;margin-left:6px}.sl .src{font-size:12px;color:var(--sub);margin:4px 0 0}
.ys{font-size:13px;color:var(--sub);font-weight:400}.ys2{margin:4px 0 0;font-size:14px;color:var(--ac2);font-weight:700}
.bars{display:grid;gap:6px}.br{display:grid;grid-template-columns:44px 1fr 110px;gap:8px;align-items:center;text-decoration:none;color:var(--ink);font-size:13.5px}
.bt{position:relative;height:18px;background:linear-gradient(180deg,rgba(232,195,122,.10),rgba(232,195,122,.02));border:1px solid rgba(232,195,122,.25);border-radius:9px;overflow:hidden}
.bt i{position:absolute;left:0;top:0;bottom:0;width:0;border-radius:9px;transition:width 1.3s cubic-bezier(.2,.8,.2,1) var(--d,0s);overflow:hidden}
.bars.on .bt i{width:var(--w)}
.b1{background:linear-gradient(135deg,rgba(255,236,196,.9) 0%,rgba(232,195,122,.8) 35%,rgba(196,150,70,.7) 60%,rgba(245,215,150,.8) 100%);
box-shadow:inset 0 0 0 1px rgba(255,255,255,.35),0 0 8px rgba(232,195,122,.35)}
.b2{background:linear-gradient(135deg,#ffd6de 0%,#ff5577 22%,#c81e4a 50%,#6e0a24 68%,#e0365c 86%,#ffc2cf 100%);
box-shadow:inset 0 0 0 1px rgba(255,255,255,.55),inset 0 -3px 6px rgba(60,0,15,.45),0 0 12px rgba(200,30,74,.7)}
.bt i::before{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(255,255,255,.65) 0%,rgba(255,255,255,.12) 45%,transparent 55%),
repeating-linear-gradient(115deg,transparent 0 10px,rgba(255,255,255,.18) 10px 12px,transparent 12px 22px);mix-blend-mode:screen}
.bt i::after{content:"";position:absolute;top:0;bottom:0;width:40px;left:-60px;background:linear-gradient(90deg,transparent,rgba(255,255,255,.85),transparent);transform:skewX(-20deg);opacity:0}
.bars.on .bt i::after{animation:shine 2.6s ease-in-out calc(var(--d,0s) + 1.3s) infinite}
@keyframes shine{0%{left:-60px;opacity:0}10%{opacity:1}60%{left:110%;opacity:.9}61%,100%{left:110%;opacity:0}}
@media (prefers-reduced-motion:reduce){.bt i{transition:none}.bars.on .bt i::after{animation:none}}.bn small{color:var(--sub);font-size:12px}
.br:hover .by{color:var(--ac2)}
.shows{margin-top:8px;border:1px solid var(--line);border-radius:10px;background:var(--bg);max-width:560px}
.shows summary{cursor:pointer;padding:6px 12px;font-size:14px;font-weight:700;color:var(--ac)}
.shows table{width:100%;border-collapse:collapse;font-size:13.5px}.shows th,.shows td{padding:5px 10px;border-top:1px solid var(--line);text-align:left;vertical-align:top}
.shows th{font-size:12px;color:var(--sub);font-weight:700}.shows td:first-child{white-space:nowrap;color:var(--sub)}
.mv{display:flex;gap:10px;align-items:center;margin-top:8px;padding:6px;border:1px solid var(--line);border-radius:10px;text-decoration:none;color:var(--ink);background:var(--bg);max-width:460px}
.mv:hover{border-color:#ff4d6a}.mv.nc:hover{border-color:#bbb}.mv.nc .th i{color:#e6e6e6;border-color:#e6e6e6}
.mvw .nl{display:inline-block;font-size:12.5px;margin:4px 0 0 4px}.mv .th{position:relative;flex:0 0 160px}.mv .th img{width:160px;aspect-ratio:16/9;object-fit:cover;border-radius:6px}
.mv .th i{position:absolute;inset:0;margin:auto;width:34px;height:24px;border-radius:7px;background:#000c;color:#ff4d6a;border:1px solid #ff4d6a;font-style:normal;font-size:12px;display:grid;place-items:center}
.mv .mt{font-size:14px;font-weight:700;line-height:1.5}.mv .mt small{display:block;font-weight:400;color:var(--sub);font-size:12px}
@media(max-width:560px){.mv .th{flex-basis:120px}.mv .th img{width:120px}}
.xpost{max-width:460px;margin-top:6px}.xpost .twitter-tweet{margin:6px 0!important}
.mosaic{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;border-radius:14px;overflow:hidden}
.mosaic a{position:relative;display:block}.mosaic img{width:100%;aspect-ratio:16/9;object-fit:cover;display:block;transition:opacity .15s}.mosaic a:hover img{opacity:.8}
@media(max-width:700px){.mosaic{grid-template-columns:repeat(2,1fr)}}
.mvgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:14px}
.mvgrid a{text-decoration:none;color:var(--ink);font-size:14px;font-weight:700;line-height:1.5}.mvgrid img{width:100%;aspect-ratio:16/9;object-fit:cover;border-radius:10px;margin-bottom:4px}
.xgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px;align-items:start}
.xgrid h3{font-size:15px;margin:0}.credit{font-size:12.5px;color:var(--sub);margin:6px 0 0}
.mg{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px;align-items:start}
.mg .c{border:1px solid var(--line);border-radius:12px;background:var(--bg);padding:14px}
.mg .c .mz{font-size:18px;font-weight:800;line-height:1.35}.mg .c .is{font-size:14px;color:var(--sub);font-weight:700}
.mg .c .dt2{font-size:12.5px;color:var(--sub);margin-top:2px}.mg .c p{font-size:14px;margin:8px 0 0}
.mg .c .k{display:inline-block;font-size:11.5px;font-weight:700;border-radius:99px;padding:0 8px;border:1px solid var(--c);color:var(--c);margin-bottom:6px}
.xbtn{display:inline-block;margin-top:10px;font:inherit;font-size:12.5px;font-weight:700;padding:3px 12px;border-radius:99px;background:#000;color:#e6e6e6;border:1px solid #e6e6e6;cursor:pointer;margin-right:6px}
.xbtn:hover{background:#1a1a1a}.mg .xwrap .xpost{max-width:100%}
.stats{display:flex;gap:10px;flex-wrap:wrap;margin-top:12px}.stats div{background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:8px 14px;text-align:center;font-size:12.5px;color:var(--sub)}
.stats b{display:block;font-size:22px;color:var(--ac2)}
.flt{display:flex;gap:6px;flex-wrap:wrap;margin:12px 0 0}.flt button{font:inherit;font-size:13.5px;padding:5px 14px;border-radius:99px;border:1px solid var(--line);background:var(--card);color:var(--ink);cursor:pointer}
.flt button.on{background:var(--ac2);border-color:var(--ac2);color:#fff}
.cv{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:14px}
.cv .c{border:1px solid var(--line);border-radius:12px;overflow:hidden;background:var(--bg)}
.cv .c img{width:100%;aspect-ratio:16/9;object-fit:cover;display:block}
.cv .c .b{padding:8px 10px 10px}.cv .c b{display:block;font-size:15px;line-height:1.45}.cv .c .d{font-size:12px;color:var(--sub)}
.cv .c .ln{display:flex;gap:6px;flex-wrap:wrap;margin-top:6px}.cv .c .ln a{font-size:12px;font-weight:700;text-decoration:none;padding:2px 9px;border-radius:99px;color:#fff}
.cv .c .ln a{background:#000;color:var(--bc);border:1px solid var(--bc)}.cv .c .ln a:hover{background:#1a1a1a}
.cv .c .ln a.y{--bc:#ff4d6a}.cv .c .ln a.n{--bc:#e6e6e6}
.cv .c .tag{display:inline-block;font-size:11px;color:var(--ac2);border:1px solid var(--ac2);border-radius:99px;padding:0 7px;margin-left:4px}
.rk{margin:0;padding-left:26px}.rk li{padding:3px 0;font-weight:700}.rk li small{color:var(--sub);font-weight:400;margin-left:8px;font-size:12.5px}
footer{background:var(--hd);color:#c8cde0;font-size:13px;text-align:center;padding:24px 16px;line-height:1.9}footer a{color:#fff}
"""


def sidebar():
    eras = "".join(f'<li><a href="{{R}}era/{e[0]}.html">{e[1]}</a></li>' for e in ERAS)
    years = "".join(f'<li><a href="{{R}}year/{y}.html">{y}年</a></li>' for y in YEARS)
    return f"""<aside class="side">
<div class="box"><h2>👑 この帝国について</h2><p class="note">CLAN QUEEN の歩みを、前身バンドの時代から今まで、あなたと一緒にたどれる<b>非公式</b>の年表サイトです。ファンがこっそりつくり、毎月のできごとごとに書き足していきます。公式とは関係ありません。</p></div>
<div class="box"><h2>🚪 WARS iN CLOSET</h2><p class="note">CLAN QUEEN の原点を、6 本の MV でたどれます。</p><ul><li><a href="{{R}}wic.html">WARS iN CLOSET の部屋（{sum(1 for k in MV if k.startswith("wic:"))} 曲）</a></li></ul></div>
<div class="box"><h2>🎸 セットリスト</h2><p class="note">あの日のライブの曲順を、もう一度たどれます。</p><ul><li><a href="{{R}}setlists.html">セットリスト まとめ（{len(SETLISTS)} 公演）</a></li></ul></div>
<div class="box"><h2>📚 雑誌インタビュー</h2><p class="note">3 人の言葉に、誌面や Web でも触れられます。</p><ul><li><a href="{{R}}magazines.html">雑誌インタビュー まとめ（{len(MAGS)} 件）</a></li></ul></div>
<div class="box"><h2>🐦 公式Xまとめ</h2><p class="note">節目の瞬間を、公式の言葉でふり返れます。</p><ul><li><a href="{{R}}x.html">公式Xまとめ（{sum(1 for e in T if e.get("x"))} 件）</a></li></ul></div>
<div class="box"><h2>🗺 時代でたどる</h2><ul>{eras}</ul></div>
<div class="box sticky"><h2>📅 年でたどる</h2><ul>{years}</ul>
<h2 style="margin-top:14px">📣 公式はこちら</h2><ul>
<li><a href="https://www.clanqueen.jp/" rel="noopener" target="_blank">CLAN QUEEN 公式サイト</a></li>
<li><a href="https://www.youtube.com/@CLAN_QUEEN" rel="noopener" target="_blank">公式 YouTube チャンネル</a></li>
<li><a href="https://x.com/clan_queen_" rel="noopener" target="_blank">公式 X（@clan_queen_）</a></li>
<li><a href="https://www.instagram.com/clanqueen/" rel="noopener" target="_blank">公式 Instagram</a></li>
<li><a href="https://www.tiktok.com/@clan_queen_" rel="noopener" target="_blank">公式 TikTok</a></li>
<li><a href="https://clanqueen-hfc.com" rel="noopener" target="_blank">ファンクラブ Hell Fire Club</a></li></ul>
<h2 style="margin-top:14px">🏠 姉妹サイト</h2><ul>
<li><a href="https://ado-himitsukichi.github.io/" rel="noopener" target="_blank">Ado 非公式ワクワク秘密基地</a></li>
<li><a href="https://yama-kossori.github.io/" rel="noopener" target="_blank">yamaファンのこっそり部屋</a></li></ul></div>
</aside>"""


def ga_tag():
    if not GA:
        return ""
    return (f'<script async src="https://www.googletagmanager.com/gtag/js?id={GA}"></script>'
            f"<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','{GA}');</script>")


def page(path, title, desc, body, crumb=None, hero=False):
    depth = path.count("/")
    R = "../" * depth
    nav = "".join(f'<li><a href="{R}{h}"{" class=on" if h == path else ""}>{t}</a></li>' for h, t in NAV)
    cr = ""
    if crumb:
        cr = '<div class="crumb"><a href="' + R + 'index.html">帝国トップ</a> › ' + " › ".join(crumb) + "</div>"
    full = NAME if path == "index.html" else f"{title}｜{NAME}"
    heroh = f'<div class="hero">{hero}</div>' if hero else ""
    og = SITE + "img/header.jpg" if os.path.exists(os.path.join(ROOT, "assets", "header.jpg")) else thumb_url(MV["WARNING!!"]["id"], "hqdefault")
    widgets = '<script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>' if "twitter-tweet" in body else ""
    doc = f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(full)}</title><meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{SITE}{path}">
<meta property="og:title" content="{esc(full)}"><meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website"><meta property="og:url" content="{SITE}{path}">
{f'<meta property="og:image" content="{og}"><meta name="twitter:card" content="summary_large_image">' if og else ''}
{ga_tag()}
<style>{CSS}</style></head><body>
<header class="top"><div class="in"><a class="logo" href="{R}index.html">CLAN QUEEN <span>秘密の</span>帝国</a><span class="badge">非公式ファンサイト</span></div></header>
<nav class="gnav"><ul>{nav}</ul></nav>
{heroh}
<div class="layout"><main>{cr}{body}</main>{sidebar()}</div>
<footer>{NAME} は、CLAN QUEEN を応援するファンによる<b>非公式</b>のファンサイトです。CLAN QUEEN・メンバーご本人・所属事務所・レーベルとは関係ありません。<br>
掲載情報は公開されている報道・公式発表をもとにしています。最新・正確な情報は<a href="https://www.clanqueen.jp/" target="_blank" rel="noopener">公式サイト</a>でご確認ください。<br>
公式の画像の複製・転載はしていません（トップのヘッダーは AI でつくったオリジナルのイラストです）。動画のサムネイルは YouTube から直接表示し、動画にリンクしています（権利は各権利者に帰属します）。 ／ <a href="{R}about.html">この帝国について・プライバシー</a><br>最終更新: {TODAY}</footer>
{widgets}</body></html>"""
    doc = doc.replace("{R}", R)
    p = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(doc)
    PAGES.append(path)


def upcoming_box(limit, title="これからの予定", more=True):
    link = '<p style="margin:10px 0 0;text-align:right"><a href="{R}schedule.html">予定をもっと見る →</a></p>' if more else ""
    return f"""<section><h2 class="sec-t">{title}</h2>
<ul class="up" id="up" data-limit="{limit}"><li class="empty">読み込み中…</li></ul>{link}
<p class="notice" style="margin-top:12px">予定は公式発表・報道をもとに毎週まとめています。変更になることがあるので、お出かけ前に公式の最新情報もあわせてご確認ください。</p></section>
<script src="{{R}}upcoming.js"></script><script>
(function(){{var el=document.getElementById('up'),lim=+el.dataset.limit,t=new Date(),pad=function(n){{return('0'+n).slice(-2)}},
today=t.getFullYear()+'-'+pad(t.getMonth()+1)+'-'+pad(t.getDate()),K={{live:'ライブ',release:'リリース',tieup:'タイアップ',event:'イベント',anniv:'記念日',media:'テレビ・ラジオ・配信',ticket:'チケット'}},
W='日月火水木金土',it=(window.CQ_UPCOMING||[]).filter(function(e){{return e.date>=today}}).slice(0,lim);
if(!it.length){{el.innerHTML='<li class="empty">いま分かっている予定はありません。</li>';return}}
el.innerHTML=it.map(function(e){{var d=new Date(e.date+'T00:00:00');return '<li><div class="d">'+(d.getMonth()+1)+'/'+d.getDate()+'<small>'+d.getFullYear()+'（'+W[d.getDay()]+'）</small></div><div><span class="k">'+(K[e.kind]||'')+'</span><div>'+e.title.replace(/[<>&]/g,'')+'</div></div></li>'}}).join('')}})();
</script>"""


def write_upcoming():
    items = []
    if os.path.exists(EVENTS_JS):
        s = open(EVENTS_JS, encoding="utf-8").read()
        for m in re.finditer(r'\{\s*date:\s*"([\d-]+)",\s*artist:\s*"CLAN QUEEN",\s*title:\s*"((?:[^"\\]|\\.)*)",\s*kind:\s*"(\w+)"', s):
            d, t, k = m.group(1), json.loads('"' + m.group(2) + '"'), m.group(3)
            if k == "anniv":
                continue
            items.append({"date": d, "title": t, "kind": k})
    items.sort(key=lambda e: e["date"])
    open(os.path.join(OUT, "upcoming.js"), "w", encoding="utf-8").write(
        "window.CQ_UPCOMING=" + json.dumps(items, ensure_ascii=False) + ";\n")
    return len(items)


def build():
    if os.path.exists(OUT):
        for n in os.listdir(OUT):
            p = os.path.join(OUT, n)
            if n == "CNAME":
                continue
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, ".nojekyll"), "w").close()
    # Gemini でつくったオリジナルのヘッダー画像（assets/header.jpg）だけを置く。公式素材はコピーしない
    if os.path.exists(os.path.join(ROOT, "assets", "header.jpg")):
        os.makedirs(os.path.join(OUT, "img"), exist_ok=True)
        shutil.copy(os.path.join(ROOT, "assets", "header.jpg"), os.path.join(OUT, "img", "header.jpg"))
    n_up = write_upcoming()

    # トップ
    era_cards = []
    for e in ERAS:
        n = sum(1 for x in T if era_of(x["date"]) == e)
        era_cards.append(f'<a class="era" href="{{R}}era/{e[0]}.html">{thumb(e[5])}'
                         f'<div class="t"><span class="n">{n} のできごと</span><b>{e[1]}</b><small>{e[2]}</small></div></a>')
    year_cards = "".join(f'<a href="{{R}}year/{y}.html">{y}<small>{sum(1 for x in T if x["date"][:4] == y)} 件</small></a>' for y in YEARS)
    # 活動のあしあと（年ごとのできごと数とライブ公演数）
    mx = max(sum(1 for x in T if x["date"][:4] == y) for y in YEARS)
    bars = ""
    bars_n = []
    for y in YEARS:
        bars_n.append(y)
        tot = sum(1 for x in T if x["date"][:4] == y); lv = sum(1 for x in T if x["date"][:4] == y and x["cat"] == "live")
        bars += (f'<a class="br" href="{{R}}year/{y}.html"><span class="by">{y}</span><span class="bt"><i class="b1" style="--w:{tot / mx * 100:.1f}%;--d:{len(bars_n) * 0.07:.2f}s"></i>'
                 f'<i class="b2" style="--w:{lv / mx * 100:.1f}%;--d:{len(bars_n) * 0.07 + 0.25:.2f}s"></i></span><span class="bn">{tot}<small>（ライブ {lv}）</small></span></a>')
    n_live = sum(1 for x in T if x["cat"] == "live")
    activity = (f'<section><h2 class="sec-t">活動のあしあと</h2><p class="lead" style="margin-bottom:10px">これまでのできごと {len(T)} 件、ライブ・フェス出演 {n_live} 公演。'
                f'年ごとにどれだけ動いてきたかを並べました（濃い赤がライブ公演）。</p><div class="bars" id="bars">{bars}</div></section>'
                '<script>(function(){var b=document.getElementById("bars");if(!b)return;function go(){b.classList.add("on")}'
                'if(!("IntersectionObserver" in window)||matchMedia("(prefers-reduced-motion: reduce)").matches){go();return}'
                'var o=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){go();o.disconnect()}})},{threshold:.25});o.observe(b)})()</script>')
    recent = [e for e in T if e["date"] <= TODAY][-6:][::-1]
    body = f"""<section><h1>ようこそ、秘密の帝国へ。</h1>
<p class="lead">CLAN QUEEN の歩みを、あなたの思い出と一緒にたどれます。前身バンド WARS iN CLOSET の 6 曲から、2022年の「ヘルファイアクラブ」での始動、『VeiL』『TOYS』『NEBULA』、歌舞伎町に約 4,000 人が集まったフリーライブ、そして初のアニメタイアップ「WARNING!!」まで。作詞・作曲・編曲から MV・グラフィック・イラストまで自分たちで形にしてきた「アートロック」の 3 人、AOi さん・yowa さん・マイさんと、一緒に作品をつくってきた作り手の皆さんへの拍手を込めて、ファンがこっそり年表にまとめた非公式の帝国です。これからも毎月、新しいできごとを書き足していきます。</p>
<p class="lead" style="margin-top:8px">あなたが CLAN QUEEN に出会った一曲は、どれですか？　見に来てくださって、ありがとうございます。</p></section>
{upcoming_box(5)}
{activity}
<section><h2 class="sec-t">時代でたどる CLAN QUEEN の歩み</h2><div class="eras">{"".join(era_cards)}</div></section>
<section><h2 class="sec-t">最近のできごと</h2>{timeline(recent, by_year=False)}
<p style="margin:6px 0 0;text-align:right"><a href="{{R}}timeline.html">全部の年表を見る →</a></p></section>
<section><h2 class="sec-t">年でたどる</h2><div class="years">{year_cards}</div></section>"""
    top = ["WARNING!!", "Whitoxin", "無花果", "MONOPOLY", "ゲルニカ", "サーチライト", "ヘルファイアクラブ", "踊楽園"]
    mosaic = '<div class="mosaic">' + "".join(
        f'<a href="{watch(MV[k]["id"])}" target="_blank" rel="noopener" title="{esc(MV[k]["title"])}"><img src="{thumb_url(MV[k]["id"])}" alt="{esc(MV[k]["title"])}"></a>'
        for k in top if k in MV) + "</div>"
    page("index.html", NAME, "アートロックバンド CLAN QUEEN の歩みを、あなたの思い出と一緒にたどれる非公式ファンサイト。前身 WARS iN CLOSET から「WARNING!!」までを年表に。ライブ・リリース・MV も。毎月更新。", body, hero=(f'<img class="hdr" src="img/header.jpg" alt="{esc(NAME)}" width="1600" height="640">' if os.path.exists(os.path.join(ROOT, "assets", "header.jpg")) else "") + mosaic)

    # 全年表
    jump = " ".join(f'<a href="#y{y}">{y}</a>' for y in YEARS)
    page("timeline.html", "全部の年表", "CLAN QUEEN の活動を、前身バンドの時代から最新ニュースまで、すべて時系列で。",
         f'<section><h1>全部の年表</h1><p class="lead">CLAN QUEEN の歩みを、最初から通してたどれます。金色の印は特に大きなできごとです。 年へジャンプ: {jump}</p></section><section>{timeline(T)}</section>',
         crumb=["全部の年表"])

    # 時代ページ
    for i, e in enumerate(ERAS):
        ev = [x for x in T if era_of(x["date"]) == e]
        pv = f'<a href="{e[0] and ERAS[i-1][0]}.html">← {ERAS[i-1][1]}</a>' if i else "<span></span>"
        nx = f'<a href="{ERAS[i+1][0]}.html">{ERAS[i+1][1]} →</a>' if i + 1 < len(ERAS) else "<span></span>"
        page(f"era/{e[0]}.html", e[1], f"CLAN QUEEN の「{e[1]}」— {e[2]}の時代を年表でたどります。",
             f'<section><a href="{watch(MV[e[5]]["id"])}" target="_blank" rel="noopener">{thumb(e[5])}</a><p class="credit">画像: 「{esc(MV[e[5]]["title"])}」のサムネイル（YouTube・{esc(MV[e[5]].get("by") or "CLAN QUEEN")} 公式チャンネル）</p><h1 style="margin-top:14px">{e[1]}</h1><p class="lead">{e[2]}</p></section>'
             f'<section>{timeline(ev)}<div class="pager">{pv}{nx}</div></section>', crumb=[e[1]])

    # 年ページ
    for i, y in enumerate(YEARS):
        ev = [x for x in T if x["date"][:4] == y]
        pv = f'<a href="{YEARS[i-1]}.html">← {YEARS[i-1]}年</a>' if i else "<span></span>"
        nx = f'<a href="{YEARS[i+1]}.html">{YEARS[i+1]}年 →</a>' if i + 1 < len(YEARS) else "<span></span>"
        page(f"year/{y}.html", f"{y}年の CLAN QUEEN", f"{y}年の CLAN QUEEN のできごと（{len(ev)}件）を年表で。",
             f'<section><h1>{y}年の CLAN QUEEN</h1><p class="lead">{len(ev)} 件のできごと</p><p class="ys2">{year_stats(y)}</p></section>'
             f'<section>{timeline(ev, by_year=False)}<div class="pager">{pv}{nx}</div></section>', crumb=[f"{y}年"])

    # カテゴリページ
    groups = {"release": {"release", "feat", "wic", "youtube"}, "live": {"live"}, "tieup": {"tieup", "media", "award"}}
    leads = {"release": "CLAN QUEEN の作品が届いた日を、順にたどれます。配信シングル・アルバム・EP・CD、メンバーの客演、前身 WARS iN CLOSET のできごと。", "live": "あの日の会場の記憶を、もう一度たどれます。ワンマンライブ・ツアー・対バン・フェス出演の記録。",
             "tieup": "あの作品で出会った一曲に、また会えます。アニメのタイアップ、テレビ・ラジオ・雑誌、受賞と記録。"}
    tv_n = sum(len(v) for v in TIEUP.values())
    leads["tieup"] += f"アニメのノンクレジット映像や主題歌入りの予告など、タイアップ先の公式 YouTube 動画 {tv_n} 本ものせています。"
    for k, t in CAT_PAGES:
        ev = [x for x in T if x["cat"] in groups[k]]
        if k == "tieup":
            ev = [with_tieup_videos(x) for x in ev]
            seen = set()  # 同じ曲の配信と CD の両方に出ないよう、タイアップ動画は最初の項目だけ
            for i, x in enumerate(ev):
                vs = [v for v in x.get("videos", []) if not (v.startswith("tieup:") and v in seen)]
                seen.update(v for v in vs if v.startswith("tieup:"))
                if vs != x.get("videos", []):
                    ev[i] = dict(x, videos=vs)
        page(f"{k}.html", t, f"CLAN QUEEN の{t}の年表。{leads[k]}",
             f'<section><h1>{t}</h1><p class="lead">{leads[k]}</p></section><section>{timeline(ev)}</section>', crumb=[t])

    # MV ギャラリー
    sec = []
    def gcard(m):
        href, src, svc = link_of(m)
        by = f'<small style="display:block;font-weight:400;color:var(--sub)">{esc(m["by"])}</small>' if m.get("by") else ""
        d = f'<small style="color:var(--sub);font-size:12px">{fmt(m["yt_date"])}</small>' if m.get("yt_date") else ""
        return f'<div><a href="{href}" target="_blank" rel="noopener"><img src="{src}" alt="" loading="lazy">{esc(m["title"])}</a>{by}{d}</div>'
    for kind, lead in [("オリジナル", "オリジナル曲の MV・リリックビデオ"), ("ライブ映像", "公式のライブ映像"), ("メイキング・特別映像", "メイキング・コンセプトフィルム"),
                       ("feat", "コラボ・客演（各アーティストの公式動画）"), ("WARS iN CLOSET", "前身 WARS iN CLOSET の MV"), ("タイアップ", "タイアップ先の公式映像")]:
        ms = sorted((m for m in MV.values() if m["kind"] == kind), key=lambda m: m.get("yt_date", ""))
        cards = "".join(gcard(m) for m in ms)
        sec.append(f'<section><h2 class="sec-t">{lead}（{len(ms)}）</h2><div class="mvgrid">{cards}</div></section>')
    page("mv.html", "MV ギャラリー", "CLAN QUEEN の MV・ライブ映像・メイキング・コラボ曲を、YouTube 公式チャンネルへのリンクでまとめました。",
         '<section><h1>MV ギャラリー</h1><p class="lead">メンバー自身が監督・編集・グラフィックまで手がける CLAN QUEEN の映像の世界を、まとめて楽しめます。サムネイルを押すと、YouTube（CLAN QUEEN 公式チャンネル・各アーティスト公式）で動画が開きます。公開された順に並べています。あなたのお気に入りの MV は、どれですか？</p></section>' + "".join(sec),
         crumb=["MV ギャラリー"])

    # WARS iN CLOSET の部屋
    cov = sorted([(k, m) for k, m in MV.items() if k.startswith("wic:")], key=lambda x: x[1]["yt_date"])
    cards = []
    for k, m in cov:
        first = ' <span class="tag">はじめての MV</span>' if (k, m) == cov[0] else ""
        cards.append(f'<div class="c"><a href="{watch(m["id"])}" target="_blank" rel="noopener"><img src="{thumb_url(m["id"])}" alt="" loading="lazy"></a><div class="b"><b>{esc(k[4:])}{first}</b>'
                     f'<span class="d">{fmt(m["yt_date"])} 公開</span><div class="ln"><a class="y" href="{watch(m["id"])}" target="_blank" rel="noopener">YouTube で見る</a></div></div></div>')
    wev = [x for x in T if x["cat"] == "wic" or era_of(x["date"]) == ERAS[0]]
    page("wic.html", "WARS iN CLOSET の部屋", f"CLAN QUEEN の前身バンド WARS iN CLOSET の MV {len(cov)} 本と、始動までの歩みをまとめました。",
         f'''<section><h1>WARS iN CLOSET の部屋</h1><p class="lead">CLAN QUEEN の原点に、あなたも一緒に立ち会えます。2020年に AOi さんとマイさんが結成した前身バンド WARS iN CLOSET が、YouTube に残した MV を公開順に並べました。この 6 曲は 2024年の EP『TOYS』で、いまの CLAN QUEEN の音で録り直されています。あなたは、どの曲が『TOYS』でいちばん化けたと思いますか？</p>
<div class="stats"><div><b>{len(cov)}</b>MV</div><div><b>2020〜2021</b>公開年</div><div><b>2022.11</b>CLAN QUEEN 始動</div></div></section>
<section><div class="cv">{"".join(cards)}</div></section>
<section><h2 class="sec-t">始動までの年表</h2>{timeline(wev)}</section>''', crumb=["WARS iN CLOSET の部屋"])

    # 予定
    # セットリスト まとめ
    cnt = {}
    for x in SETLISTS:
        for sg in x["songs"]:
            if sg.get("t"):
                cnt[sg["t"]] = cnt.get(sg["t"], 0) + 1
    top_songs = sorted(cnt.items(), key=lambda kv: -kv[1])[:10]
    rank = "".join(f'<li>{esc(k)}<small>{v} 公演</small></li>' for k, v in top_songs)
    ev_of = {}
    for e in T:
        if e["cat"] in ("live", "milestone", "media"):
            ev_of.setdefault(e["date"], e)
    rows = []
    for x in sorted(SETLISTS, key=lambda x: x["date"], reverse=True):
        e = ev_of.get(x["date"])
        name = esc(e["title"]) if e else "ライブ"
        body, n = setlist_body(x["songs"])
        rows.append(f'<li class="ev"><div class="dt">{fmt(x["date"])}</div><div class="bd"><h3>{name}</h3>'
                    f'<details class="sl"><summary>セットリスト（{n} 曲）</summary>{body}<p class="src">出典: <a href="{esc(x["url"])}" target="_blank" rel="noopener">setlist.fm</a></p></details></div></li>')
    page("setlists.html", "セットリスト まとめ", f"CLAN QUEEN のライブ {len(SETLISTS)} 公演のセットリストを、setlist.fm のファンの記録から日本語の曲名でまとめました。",
         f'''<section><h1>セットリスト まとめ</h1><p class="lead">あの日のライブの曲順を、もう一度たどれます。ワンマン・ツアー・フェスの {len(SETLISTS)} 公演のセットリストを、新しい順に並べました。setlist.fm にファンが投稿した記録をもとに、曲名を日本語にしています。記録を残してくれたファンの皆さんに感謝を込めて。あなたがいちばん心に残っている一曲は、どれですか？</p>
<div class="stats"><div><b>{len(SETLISTS)}</b>公演</div><div><b>{len(cnt)}</b>曲</div><div><b>{min(x["date"] for x in SETLISTS)[:4]}〜{max(x["date"] for x in SETLISTS)[:4]}</b>年</div></div>
<p class="notice" style="margin-top:12px">公式発表ではないため、実際と違う場合があります。曲名が確認できなかったものは setlist.fm の表記のままです。</p></section>
<section><h2 class="sec-t">よく演奏されている曲 TOP10</h2><ol class="rk">{rank}</ol></section>
<section><h2 class="sec-t">公演ごとのセットリスト</h2><ol class="tl">{"".join(rows)}</ol></section>''', crumb=["セットリスト まとめ"])

    # 公式 X まとめ
    xs = [e for e in T if e.get("x")][::-1]
    cards = "".join(f'<div><h3>{fmt(e["date"])}｜{esc(e["title"])}</h3>{x_embed(e["x"])}</div>' for e in xs)
    page("x.html", "公式Xまとめ", "CLAN QUEEN の公式 X から、始動・リリース・メジャーデビュー・タイアップなど節目のポストを埋め込みでまとめました。",
         '<section><h1>公式Xまとめ</h1><p class="lead">節目の瞬間を、公式の言葉でふり返れます。リリース・メジャーデビュー・タイアップなど節目のポストを、X の埋め込みで新しい順に並べています。最新の情報は '
         '<a href="https://x.com/clan_queen_" target="_blank" rel="noopener">@clan_queen_</a> をご覧ください。</p></section>'
         f'<section><div class="xgrid">{cards}</div></section>', crumb=["公式Xまとめ"])

    # 雑誌インタビュー
    KC = {"表紙・巻頭": "#e0457b", "表紙": "#e0457b", "インタビュー": "#2563eb", "対談": "#8b5cf6", "特集": "#ca8a04",
          "ライブレポート": "#16a34a", "Web インタビュー": "#0891b2", "連載": "#9f1239"}
    myears = sorted({e["date"][:4] for e in MAGS})
    mblocks = []
    for y in myears:
        cards = []
        for e in [x for x in MAGS if x["date"][:4] == y]:
            grp = "web" if e["kind"].startswith("Web") or not e["on_sale"] else "print"
            dl = ("発売 " if e["on_sale"] else "公式 X で告知 ") + fmt(e["date"])
            btns = "".join(f'<button class="xbtn" data-x="{esc(u)}">公式 X のポストを表示</button>' for u in e["x"])
            cards.append(f'<div class="c" data-g="{grp}"><span class="k" style="--c:{KC.get(e["kind"], "#475569")}">{esc(e["kind"])}</span>'
                         f'<div class="mz">{esc(e["magazine"])}</div><div class="is">{esc(e["issue"])}</div><div class="dt2">{dl}</div>'
                         f'<p>{esc(e["note"])}</p>{btns}<div class="xwrap"></div></div>')
        mblocks.append(f'<section class="yb"><h2 class="yr" id="m{y}">{y}年 <small style="font-size:14px;color:var(--sub)">{len(cards)} 件</small></h2><div class="mg">{"".join(cards)}</div></section>')
    n_print = sum(1 for e in MAGS if e["on_sale"])
    n_mag = len({e["magazine"] for e in MAGS})
    jump = " ".join(f'<a href="#m{y}">{y}</a>' for y in myears)
    page("magazines.html", "雑誌インタビュー", f"CLAN QUEEN の雑誌・Web のインタビューや連載・対談 {len(MAGS)} 件を、公式 X と公式サイトの告知からまとめました。",
         f'''<section><h1>雑誌インタビュー</h1><p class="lead">3 人の言葉に、誌面や Web でもっと触れられます。公式 X（@clan_queen_）と公式サイトで告知された、雑誌・Web メディアのインタビュー・連載・対談をまとめました。ボタンを押すと、その公式ポストが X の埋め込みで表示されます。記事・誌面の内容は各メディアでお楽しみください。</p>
<div class="stats"><div><b>{len(MAGS)}</b>掲載</div><div><b>{n_print}</b>雑誌（紙）</div><div><b>{n_mag}</b>媒体</div><div><b>{myears[0]}〜{myears[-1]}</b>年</div></div>
<div class="flt"><button class="on" data-f="all">すべて</button><button data-f="print">雑誌（紙）</button><button data-f="web">Web</button></div>
<p style="margin:10px 0 0;font-size:14px">年へジャンプ: {jump}</p>
<p class="notice" style="margin-top:12px">マイさんは「Rolling Stone Japan」で連載「MAILOG」を続けています。発売日は公式の告知に書かれた日付、「公式 X で告知」は告知ポストの日付です。見つかりしだい毎月書き足します。</p></section>
{"".join(mblocks)}
<script>document.querySelectorAll('.flt button').forEach(function(b){{b.onclick=function(){{document.querySelectorAll('.flt button').forEach(function(x){{x.classList.toggle('on',x===b)}});var f=b.dataset.f;
document.querySelectorAll('.mg .c').forEach(function(c){{c.style.display=(f==='all'||c.dataset.g===f)?'':'none'}});
document.querySelectorAll('.yb').forEach(function(s){{s.style.display=[].some.call(s.querySelectorAll('.c'),function(c){{return c.style.display!=='none'}})?'':'none'}})}}}});
document.querySelectorAll('.xbtn').forEach(function(b){{b.onclick=function(){{var w=b.parentNode.querySelector('.xwrap');if(b.dataset.done){{return}}b.dataset.done=1;b.textContent='表示しました';
var d=document.createElement('div');d.className='xpost';d.innerHTML='<blockquote class="twitter-tweet" data-lang="ja" data-dnt="true"><a href="'+b.dataset.x+'"></a></blockquote>';w.appendChild(d);
function go(){{window.twttr&&twttr.widgets?twttr.widgets.load(d):setTimeout(go,300)}}if(!window.__tw){{window.__tw=1;var s=document.createElement('script');s.src='https://platform.twitter.com/widgets.js';s.async=true;document.body.appendChild(s)}}go()}}}});</script>''',
         crumb=["雑誌インタビュー"])

    page("schedule.html", "これからの予定", "CLAN QUEEN のこれからのライブ・リリース・フェス出演などの予定。毎週更新。",
         '<section><h1>これからの予定</h1><p class="lead">次に CLAN QUEEN に会える日が、ひと目でわかります。ライブ・フェス・リリース・チケットの予定をまとめています。</p></section>'
         + upcoming_box(80, "予定一覧", more=False), crumb=["これからの予定"])

    # この部屋について
    page("about.html", "この帝国について", "CLAN QUEEN 秘密の帝国について、運営方針とプライバシーポリシー。", """<section><h1>この帝国について</h1>
<p>「CLAN QUEEN 秘密の帝国」は、CLAN QUEEN の歩みを、ファンのあなたが好きなときにたどれるようにつくった<b>非公式</b>のファンサイトです。CLAN QUEEN・メンバーご本人、所属事務所、レーベル（Princidom Records／Sony Music Labels）とは一切関係ありません。</p>
<h2>この帝国でやっていること</h2><ul>
<li>前身バンド WARS iN CLOSET の時代から今までのできごとを、年表にまとめています。ライブは 1 公演ずつ年表にのせています</li>
<li>毎月、前の月のできごとを書き足します。これからの予定は毎週更新します</li>
<li>情報は公式サイト・公式 YouTube・公式 X・報道・Wikipedia などの公開情報と、ライブ記録サイト（setlist.fm）をもとにしています。まちがいに気づいたときは直します</li></ul>
<h2>セットリストについて</h2>
<p>「セットリスト」ボタンの中身は、setlist.fm にファンが投稿した記録をもとに、曲名を日本語に直したものです。公式発表ではないため、実際と違う場合があります。曲名が確認できなかったものは、setlist.fm の表記のままにしています。</p>
<h2>やらないこと</h2><ul>
<li>広告・アフィリエイトは載せません</li>
<li>歌詞の引用、公式の写真・イラスト・ロゴの複製・転載はしません。画像は、YouTube の公式動画のサムネイル（YouTube から直接表示し、動画にリンク）と、Gemini でつくったオリジナルのヘッダーイラスト（メンバーご本人や公式ロゴは描いていません）だけです。権利は各権利者に帰属します。削除のご依頼があればすぐに対応します</li>
<li>メンバーの私生活に関することや、うわさ話は書きません</li></ul>
<h2>見に来てくださって、ありがとうございます</h2>
<p>音も映像もビジュアルも自分たちの手で形にしてきた AOi さん・yowa さん・マイさん、作品づくりに関わる作り手の皆さん、そして応援を続けるファンの皆さんに、心から感謝しています。この帝国が、あなたの「好き」をもう一度たしかめる場所になればうれしいです。</p>
<p>あなたの好きな CLAN QUEEN の曲は、何ですか？</p>
<h2>プライバシーポリシー</h2>
<p>動画のサムネイルは YouTube（Google）から直接表示しているため、YouTube が Cookie などで情報を取得する場合があります。アクセスの傾向を知るために Google アナリティクスを使っています。Cookie を使って匿名のアクセス情報を集めますが、個人を特定する情報は集めません。ブラウザの設定で Cookie を無効にできます。</p>
<h2>参考にしている情報源</h2><ul>
<li><a href="https://www.clanqueen.jp/" target="_blank" rel="noopener">CLAN QUEEN 公式サイト</a>（INFORMATION・LIVE・BIOGRAPHY）</li>
<li><a href="https://www.youtube.com/@CLAN_QUEEN" target="_blank" rel="noopener">CLAN QUEEN 公式 YouTube</a></li>
<li><a href="https://www.setlist.fm/setlists/clan-queen-2be13416.html" target="_blank" rel="noopener">CLAN QUEEN - setlist.fm</a>（セットリスト）</li>
<li><a href="https://x.com/clan_queen_" target="_blank" rel="noopener">CLAN QUEEN 公式 X</a></li>
<li><a href="https://ja.wikipedia.org/wiki/CLAN_QUEEN" target="_blank" rel="noopener">CLAN QUEEN - Wikipedia</a></li>
<li>音楽ナタリー、Rolling Stone Japan、Real Sound、Billboard JAPAN、rockinon.com などの音楽ニュース</li></ul></section>""", crumb=["この帝国について"])

    # sitemap / robots
    sm = "".join(f"<url><loc>{SITE}{'' if p == 'index.html' else p}</loc><lastmod>{TODAY}</lastmod></url>" for p in PAGES)
    open(os.path.join(OUT, "sitemap.xml"), "w").write(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>')
    open(os.path.join(OUT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {SITE}sitemap.xml\n")
    print(f"built {len(PAGES)} pages, {len(T)} timeline events, {n_up} upcoming")


PAGES = []
if __name__ == "__main__":
    build()
