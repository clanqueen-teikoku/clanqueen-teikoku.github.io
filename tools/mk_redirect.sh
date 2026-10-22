#!/bin/sh
# 旧住所の転送ページを作る: tools/mk_redirect.sh <転送用リポジトリのフォルダ>
# docs/ の全ページについて、同じパスに新しい住所 https://clanqueen-teikoku.github.io/ への転送ページを書く。
R="$1"; NEW="https://clanqueen-teikoku.github.io/"
cd "$(dirname "$0")/../docs" || exit 1
find . -name "*.html" | while read f; do
  p=${f#./}; mkdir -p "$R/docs/$(dirname "$p")"
  u="$NEW$p"; [ "$p" = index.html ] && u="$NEW"
  printf '<!doctype html><html lang="ja"><head><meta charset="utf-8"><title>CLAN QUEEN 秘密の帝国へ移転しました</title><link rel="canonical" href="%s"><meta http-equiv="refresh" content="0; url=%s"><meta name="robots" content="noindex"></head><body><p>このサイトは「CLAN QUEEN 秘密の帝国」<a href="%s">%s</a> に移転しました。</p></body></html>\n' "$u" "$u" "$u" "$u" > "$R/docs/$p"
done
cp "$R/docs/index.html" "$R/docs/404.html"; touch "$R/docs/.nojekyll"
