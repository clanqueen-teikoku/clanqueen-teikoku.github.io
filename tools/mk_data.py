#!/usr/bin/env python3
"""集めた元データ（data/raw/）から data/mv.json・data/timeline.json を作る。

- data/raw/raw_videos.json  … CLAN QUEEN 公式 YouTube の全動画（tools/yt_uploads.py + tools/yt_dates.py）
- data/raw/extra_raw.json   … 前身 WARS iN CLOSET の公式 MV と、ほかのアーティスト公式チャンネルの feat. 動画
- data/raw/sony_live.json   … 公式サイト（Sony Music）のライブ一覧（2025年の NEBULA ツアー以降）
                               https://www.sonymusic.co.jp/json/v2/artist/clanqueen-hp/live/start/0/count/100（Referer が要る）
- data/core.json            … 手で書いた節目のできごと（結成・リリース・タイアップ・初期のライブなど）。1 行 1 件
毎月の更新では core.json に足すか、raw を取り直してこのスクリプト → build.py の順に走らせる。
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = lambda p: json.load(open(os.path.join(ROOT, p), encoding="utf-8"))

# 公式ライブ一覧の公演名 → 年表での名前・ひとこと・大きなできごとか（自分たちのツアー・主催）
OWN = {
    "CLAN QUEEN 2nd ONEMAN TOUR NEBULA": ("CLAN QUEEN 2nd ONEMAN TOUR「NEBULA」", "2nd アルバム『NEBULA』を携えたワンマンツアー。追加公演は KT Zepp Yokohama。"),
    "CLAN QUEEN 2MAN LIVE \"MIRAGRAM\"": ("CLAN QUEEN 2MAN LIVE「MIRAGRAM」", "初の 2 マンライブ。横浜は THE ORAL CIGARETTES、大阪は yama をゲストに迎えました。"),
    "CLAN QUEEN \"Grand Hotel MONOPOLY Tour\" 2026": ("CLAN QUEEN「Grand Hotel MONOPOLY Tour」2026", "札幌から東京まで、東名阪の Zepp を含む全国ツアー。福岡は追加公演で 2 日間に。東京公演は「WARNING!!」の完全生産限定盤に映像が収録されます。"),
    "CLAN QUEEN ONEMAN LIVE 2026「Secret Empire」": ("CLAN QUEEN ONEMAN LIVE 2026「Secret Empire」", "東京ガーデンシアターでの、過去最大規模のワンマン。"),
    "CLAN QUEEN HALL TOUR 2027": ("CLAN QUEEN HALL TOUR 2027", "初のホールツアー。福岡から SGC HALL ARIAKE まで全 5 か所。"),
}
BIG_FES = re.compile(r"ROCK IN JAPAN|SUMMER SONIC|COUNTDOWN JAPAN|VIVA LA ROCK|JAPAN JAM|RADIO CRAZY|SWEET LOVE SHOWER|METROPOLITAN")
TV = re.compile(r"バズリズム")
# その日の公式ライブ映像（mv.json のキー）
SHOW_VIDEOS = {"2025-07-12": ["live:SPEED（NEBULA Zepp Shinjuku）"],
               "2025-08-23": ["live:MONOPOLY（NEBULA KT Zepp Yokohama）", "live:サーチライト（NEBULA KT Zepp Yokohama）"],
               "2026-05-15": ["live:踊楽園（Grand Hotel MONOPOLY Tour Zepp DiverCity）", "live:Grand Hotel MONOPOLY Tour（YouTube Music Weekend Edit）"]}


def q(t):
    m = re.search(r'["“”]\s*(.+?)\s*["“”]', t)
    return m.group(1).strip() if m else ""


def mk_mv():
    mv = {}
    for v in sorted(J("data/raw/raw_videos.json"), key=lambda v: v["date"]):
        t = v["title"]
        if re.search(r"Teaser|ティザー", t):
            continue
        if "Weekend Edit" in t:
            mv["live:Grand Hotel MONOPOLY Tour（YouTube Music Weekend Edit）"] = {"id": v["id"], "title": t, "kind": "ライブ映像", "yt_date": v["date"]}
            continue
        if re.search(r"\bLIVE\b", t):
            where = ("NEBULA Zepp Shinjuku" if "Shinjuku" in t else "NEBULA KT Zepp Yokohama" if "Yokohama" in t else
                     "PARADE OF TOYS WWW X" if "PARADE" in t else "FREE LIVE『99』" if "99" in t else "Grand Hotel MONOPOLY Tour Zepp DiverCity")
            mv[f"live:{q(t)}（{where}）"] = {"id": v["id"], "title": t, "kind": "ライブ映像", "yt_date": v["date"]}
            continue
        if re.search(r"Behind|Concept Film", t):
            name = q(t)
            mv[f"extra:{name}（{'Concept Film' if 'Concept' in t else 'Behind'}）"] = {"id": v["id"], "title": t, "kind": "メイキング・特別映像", "yt_date": v["date"]}
            continue
        song = q(t)
        if not song:
            continue
        old = mv.get(song)
        if old and "Lyric" not in old["title"]:
            continue
        mv[song] = {"id": v["id"], "title": t, "kind": "オリジナル", "yt_date": v["date"]}
    for f in J("data/raw/extra_raw.json"):
        key = ("wic:" if f["kind"] == "WARS iN CLOSET" else "feat:") + f["song"]
        mv[key] = {"id": f["id"], "title": f["title"], "kind": f["kind"], "by": f["by"], "yt_date": f["date"]}
    return mv


def mk_lives():
    ev = []
    for it in J("data/raw/sony_live.json")["items"]:
        name = re.sub(r"\s+", " ", it["tourName"]).strip()
        if "振替" in name:
            continue
        shows = []
        for x in it.get("liveItem", []):
            d = x["date"].replace(".", "-")
            s = {"date": d, "place": "韓国" if x["area"] == "その他" else x["area"], "venue": re.sub(r"^韓国\s*", "", x["place"]).strip()}
            if SHOW_VIDEOS.get(d):
                s["videos"] = SHOW_VIDEOS[d]
            shows.append(s)
        if not shows:
            continue
        shows.sort(key=lambda s: s["date"])
        if "PLAYPARK" in name:  # 名古屋公演は 12/30 に振替
            shows = [s for s in shows if s["date"] != "2025-12-07"] + [{"date": "2025-12-30", "place": "愛知県", "venue": "Zepp Nagoya（振替公演）"}]
        own = OWN.get(name)
        if own:
            title, note, big = f"『{own[0]}』", own[1], True
        else:
            clean = re.sub(r"\s*\(yowa\)$", "", name)
            title = ("yowa が" if name.endswith("(yowa)") else "") + f"「{clean}」に出演"
            note, big = "", bool(BIG_FES.search(name))
            if "PLAYPARK" in name:
                note = "muque 主催のイベント。名古屋公演は 12 月 30 日に振替。"
        cat = "media" if TV.search(name) else "live"
        e = {"date": shows[0]["date"], "cat": cat, "title": title, "note": note, "big": big}
        if len(shows) > 1:
            e["shows"] = shows
        else:
            e["note"] = f"{shows[0]['place']}・{shows[0]['venue']}。" + note
            if shows[0].get("videos"):
                e["videos"] = shows[0]["videos"]
        ev.append(e)
    return ev


MV = mk_mv()
if __name__ == "__main__":
    T = J("data/core.json") + mk_lives()
    for e in T:
        for k in e.get("videos", []) + [v for s in e.get("shows", []) for v in s.get("videos", [])]:
            if k not in MV:
                print("videos: mv.json に無い", e["date"], k)
    T.sort(key=lambda e: e["date"])
    json.dump(MV, open(os.path.join(ROOT, "data", "mv.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(T, open(os.path.join(ROOT, "data", "timeline.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"mv {len(MV)}, timeline {len(T)}（ツアー公演の展開前）")
