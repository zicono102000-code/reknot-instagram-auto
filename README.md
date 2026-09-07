# RE:KNOT Instagram 自動投稿

RE:KNOT(呉市のクリーニング店)のInstagram投稿を、Claude Codeのクラウドスケジュール機能で自動化する仕組み。

## 仕組み

1. `/queue` フォルダに投稿したい写真を追加してpushする
2. Claude Codeのクラウドルーティンが週3回(月・水・金 12:00 JST)実行される:
   - `/queue` 内で最も古い写真を1枚選ぶ(無ければ何もしない)
   - `automation/brand_voice.md` を参照し、写真を見てRE:KNOTのトーンに沿ったキャプション+ハッシュタグを生成
   - `automation/post_to_instagram.py` でInstagramに投稿
   - 成功したら写真を `/posted` に移動し、`log/history.json` に記録してcommit・push

## フォルダ構成

- `queue/` — 投稿待ちの写真を置く場所
- `posted/` — 投稿済み写真のアーカイブ
- `automation/post_to_instagram.py` — Instagram Graph APIへの投稿処理
- `automation/refresh_token.py` — アクセストークンの延長(60日ごと)
- `automation/brand_voice.md` — キャプション生成時に参照するブランドトーン資料
- `automation/SETUP_GUIDE.md` — Instagram/Meta側の初期セットアップ手順
- `log/history.json` — 投稿履歴

## 注意事項

- このリポジトリはpublicです。`/queue` と `/posted` に置く写真は、Instagram投稿用の公開URLを得るために公開されます(いずれ投稿として公開される素材のみを置いてください)。
- Instagramのアクセストークン・アカウントIDは、このリポジトリには一切含めません。クラウドルーティンの実行設定に別途渡しています。
