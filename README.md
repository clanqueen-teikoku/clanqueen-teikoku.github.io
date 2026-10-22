# CLAN QUEEN 秘密の帝国（非公式ファンサイト）

アートロックバンド CLAN QUEEN の歩みを、前身 WARS iN CLOSET の時代から今まで年表にまとめた非公式ファンサイト。
公開先: https://clanqueen-teikoku.github.io/
保管庫（リポジトリ）: clanqueen-teikoku/clanqueen-teikoku.github.io（GitHub 組織 clanqueen-teikoku）
つくりは「Ado 非公式ワクワク秘密基地」（~/ado-himitsukichi）・「yamaファンのこっそり部屋」（~/yama-kossori）と同じ。

- `data/core.json` … 手で書く節目のできごと（1 行 1 件。毎月、前の月のできごとを追記）
- `python3 tools/mk_data.py` … 公式 YouTube（data/raw/raw_videos.json）・前身バンドと feat. の公式動画（data/raw/extra_raw.json）・
  公式サイトのライブ一覧（data/raw/sony_live.json）・core.json から `data/mv.json` / `data/timeline.json` を作る
- `python3 build.py` … docs/ を生成（これからの予定は ~/knowledge-os/oshi-events.js の CLAN QUEEN 分）
- 元データの取り直し:
  - YouTube: `python3 tools/yt_uploads.py videos > data/raw/raw_videos.json` → `python3 tools/yt_dates.py`
  - ライブ: `curl -s -A Mozilla/5.0 -e https://www.clanqueen.jp/live/ https://www.sonymusic.co.jp/json/v2/artist/clanqueen-hp/live/start/0/count/100 | sed -E 's/^callback\(//; s/\);?$//' > data/raw/sony_live.json`
  - お知らせ: 同じ形で `.../information/...` → data/raw/sony_information.json（core.json に足すネタ探し用）
- 画像ファイルは置かない。MV は YouTube サムネイルを直接表示して公式動画にリンク
- 広告・アフィリエイトなし。歌詞の引用なし。Google アナリティクスはほかのサイトと共通の測定 ID（ホスト名 clanqueen-teikoku.github.io で絞る）

旧住所 masabee1029.github.io/clanqueen-himitsukichi/ と masabee1029.github.io/clanqueen-teikoku/ は転送ページだけ（~/clanqueen-himitsukichi-redirect・~/clanqueen-teikoku-redirect。tools/mk_redirect.sh で作り直せる）。新しいページを足したら転送ページも作り直す
