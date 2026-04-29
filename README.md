# vibe-coding-records

「中小企業のひとりDX担当が、AIで会社をアップデートする」シリーズの記事制作パイプラインと、公開記事のアーカイブです。

## このリポジトリの目的

- 個人noteで連載する記事のMarkdown原本管理
- 記事に使う画像（SVG資産＋PNG配信用）のホスティング
- Markdown→note(WXR)変換、SVG→PNG変換、Playwrightキャプチャなどのパイプライン

## 構成

```
vibe-coding-records/
├─ articles/         公開記事のMarkdown
├─ images/
│   ├─ svg/         SVG資産（編集可能ソース）
│   └─ png/         note配信用PNG（GitHub Pages経由で公開）
├─ scripts/         パイプライン用スクリプト
└─ wxr/             noteインポート用WXRファイル
```

## 画像配信URL

`images/png/` 配下のファイルは GitHub Pages で公開されます。
URL例: `https://haryukin9.github.io/vibe-coding-records/images/png/example.png`
