# Instagram自動投稿 セットアップガイド(Meta/Instagram側)

このガイドはアカウント作成・ログインを伴うため、必ずご本人が操作してください。詰まったところがあれば画面を教えていただければ一緒に確認します。

必要なもの: Instagramアカウント、Facebookアカウント(RE:KNOT運営用に用意、既存の個人アカウントで代用も可)

## ステップ1: Instagramをプロアカウントにする

1. Instagramアプリ → プロフィール画面 → 右上メニュー → 「アカウントの種類とツール」
2. 「プロアカウントに切り替える」を選択
3. カテゴリを選択(例:「クリーニング店」「衣料品店」等、近いものでOK)
4. 「ビジネス」を選択(「クリエイター」ではなくビジネス)

## ステップ2: Facebookページと連携する

1. プロアカウント設定の流れの中で「Facebookページと連携」を選べる場合はそのまま進める
2. 連携できるページがなければ、Facebookで新規ページを作成(ページ名: RE:KNOT など)してから連携する
3. 連携後、Instagram側の設定 →「アカウントセンター」→「アカウントとプロフィールの連携」でFacebookページとの連携が「連携済み」になっていることを確認

## ステップ3: Metaアプリを作成する

1. https://developers.facebook.com/apps/ にアクセスし、Facebookアカウントでログイン
2. 「アプリを作成」→ アプリタイプは「ビジネス」を選択
3. アプリ名(例: RE:KNOT Instagram Automation)を入力して作成
4. 作成後のダッシュボードで「製品を追加」→ **Instagram** を追加(Instagram Graph API/Instagram APIの製品)
5. 左メニューの「設定」→「基本設定」で **App ID** と **App Secret** をメモしておく(あとで`refresh_token.py`に使う)

## ステップ4: アクセストークンを発行する

1. Metaアプリのダッシュボード内「ツール」→「Graph API Explorer」を開く
2. 右上の「User or Page」で対象のFacebookページを選択
3. 「Permissions」に以下を追加:
   - `instagram_basic`
   - `instagram_content_publish`
   - `pages_show_list`
   - `pages_read_engagement`
4. 「Generate Access Token」を押し、認可ダイアログでRE:KNOTのFacebookページとInstagramアカウントへのアクセスを許可
5. 発行された(短期の)トークンをコピーする
6. これは短期トークンなので、長期トークン(60日)に交換する。ブラウザで以下のURLを開く(`{}`部分は実際の値に置き換え):

   ```
   https://graph.facebook.com/v21.0/oauth/access_token?grant_type=fb_exchange_token&client_id={App ID}&client_secret={App Secret}&fb_exchange_token={ステップ4-5でコピーした短期トークン}
   ```

7. レスポンスのJSON内`access_token`が長期トークン。これをメモしておく(以後`IG_ACCESS_TOKEN`として使う)

## ステップ5: InstagramビジネスアカウントIDを取得する

1. Graph API Explorerで、下記のリクエストを長期トークン付きで実行:
   ```
   GET /me/accounts?access_token={長期トークン}
   ```
2. レスポンスからRE:KNOTのFacebookページの`id`(ページID)を確認
3. 続けて以下を実行:
   ```
   GET /{ページID}?fields=instagram_business_account&access_token={長期トークン}
   ```
4. レスポンス内`instagram_business_account.id`がInstagramビジネスアカウントID(以後`IG_USER_ID`として使う)

## ステップ6: 動作確認(手元で1回テスト)

以下のコマンドで、実際に1枚テスト投稿できるか確認する(画像URLは一時的に公開されている任意の画像で可):

```bash
python automation/post_to_instagram.py \
  --image-url "https://raw.githubusercontent.com/xxxx/xxxx/main/queue/test.jpg" \
  --caption "テスト投稿です" \
  --ig-user-id "{IG_USER_ID}" \
  --access-token "{IG_ACCESS_TOKEN}"
```

成功すると投稿のmedia idが出力され、Instagramのプロフィールに投稿が反映される。

## 取得した値の受け渡し

`IG_USER_ID` と `IG_ACCESS_TOKEN` は**このリポジトリには書き込まない**。Claude Codeのスケジュールルーティンを作成する際に、そのルーティンの実行設定として直接渡す(私と一緒に作業する際にチャットで共有していただく)。

## トークンの更新(60日ごと)

長期トークンは60日で失効する。失効前に以下を実行すると新しい60日トークンが発行される:

```bash
python automation/refresh_token.py --app-id {App ID} --app-secret {App Secret} --current-token {現在のトークン}
```

出力された新しいトークンを、ルーティン設定に反映する(私に伝えていただければ更新します)。
