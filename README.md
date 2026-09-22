# RE:KNOT Instagram 自動投稿

RE:KNOT(呉市のクリーニング店)のInstagram投稿を、Claude Codeのクラウドスケジュール機能で自動化する仕組み。

## 仕組み

キャプション生成(Claude)と実際のInstagram投稿(GitHub Actions)を分離している。
Claude Codeのクラウド実行環境はネットワークポリシー上 `graph.instagram.com` に
接続できないため、投稿処理だけをGitHub Actionsランナーに任せている。

1. `/queue` フォルダに投稿したい写真を追加してpushする
2. Claude Codeのクラウドルーティンが週3回(月・水・金 12:00 JST)実行される:
   - `/queue` 内で最も古い写真(キャプション未作成のもの)を1枚選ぶ(無ければ何もしない)
   - `automation/brand_voice.md` を参照し、写真を見てRE:KNOTのトーンに沿ったキャプション+ハッシュタグを生成
   - 同名+`.caption.txt` のファイル(例: `queue/xxx.jpg.caption.txt`)としてキャプションを保存し、commit・push
3. `.github/workflows/auto-post.yml` が起動する(pushトリガー/15分おきのスケジュール/手動実行のいずれか):
   - `automation/publish_next.py` が `/queue` 内でキャプションファイルが揃っている最も古い画像を1件選ぶ
   - `automation/post_to_instagram.py` のロジックでInstagramに投稿
   - 成功したら写真を `/posted` に移動し、キャプションファイルを削除し、`log/history.json` に記録してcommit・push
   - 失敗した場合は何もcommitせず終了し、次回実行時に自動的にリトライされる

## フォルダ構成

- `queue/` — 投稿待ちの写真を置く場所(`*.caption.txt` はキャプション準備済みの合図)
- `posted/` — 投稿済み写真のアーカイブ
- `automation/post_to_instagram.py` — Instagram Graph APIへの投稿処理(コンテナ作成・公開の共通ロジック)
- `automation/publish_next.py` — GitHub Actionsから実行される、queue内の1件を選んで投稿するスクリプト
- `automation/refresh_token.py` — アクセストークンの延長(60日ごと)
- `automation/brand_voice.md` — キャプション生成時に参照するブランドトーン資料
- `automation/SETUP_GUIDE.md` — Instagram/Meta側の初期セットアップ手順
- `.github/workflows/auto-post.yml` — 実際の投稿を実行するGitHub Actionsワークフロー
- `log/history.json` — 投稿履歴

## 注意事項

- このリポジトリはpublicです。`/queue` と `/posted` に置く写真は、Instagram投稿用の公開URLを得るために公開されます(いずれ投稿として公開される素材のみを置いてください)。
- Instagramのアクセストークン・アカウントIDは、このリポジトリには一切含めません。GitHub Actionsのリポジトリシークレット(`IG_USER_ID` / `IG_ACCESS_TOKEN`)として設定してください(Settings → Secrets and variables → Actions)。
