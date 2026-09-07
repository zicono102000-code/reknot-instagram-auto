# -*- coding: utf-8 -*-
"""Instagram API(Instagram Login方式)投稿スクリプト(標準ライブラリのみ・pip不要)

使い方:
    python post_to_instagram.py --image-url https://.../photo.jpg --caption "キャプション本文" \
        --ig-user-id 28538506969107764 --access-token IGAA...

    # アクセストークン/IDは環境変数からも読み込み可能
    #   IG_USER_ID, IG_ACCESS_TOKEN

流れ:
    1. POST /{ig-user-id}/media          画像URL+キャプションでメディアコンテナを作成
    2. GET  /{container-id}?fields=status_code  コンテナの処理完了を待つ(最大30秒)
    3. POST /{ig-user-id}/media_publish  コンテナを公開(実際に投稿される)

成功すると投稿のmedia idを標準出力に1行で出す(呼び出し側がログに使う)。

注意: 2024年以降のMeta「Instagram API with Instagram Login」方式を使用しており、
エンドポイントは graph.facebook.com ではなく graph.instagram.com。
アクセストークンはMeta開発者ダッシュボードの「アクセストークンを生成」ボタン、
または refresh_token.py で更新したものを使う(IGAAで始まる文字列)。
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API_VERSION = "v21.0"
BASE_URL = f"https://graph.instagram.com/{API_VERSION}"


def _post(path: str, params: dict) -> dict:
    url = f"{BASE_URL}/{path}"
    data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            return json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        sys.exit(f"Graph APIエラー (HTTP {e.code}) at {path}:\n{detail}")


def _get(path: str, params: dict) -> dict:
    url = f"{BASE_URL}/{path}?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=30) as res:
            return json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        sys.exit(f"Graph APIエラー (HTTP {e.code}) at {path}:\n{detail}")


def create_container(ig_user_id: str, image_url: str, caption: str, access_token: str) -> str:
    result = _post(
        f"{ig_user_id}/media",
        {"image_url": image_url, "caption": caption, "access_token": access_token},
    )
    if "id" not in result:
        sys.exit(f"メディアコンテナの作成に失敗しました: {result}")
    return result["id"]


def wait_until_ready(container_id: str, access_token: str, timeout_sec: int = 30) -> None:
    """コンテナのstatus_codeがFINISHEDになるまで待つ(画像URL取得が遅い場合の保険)"""
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        result = _get(container_id, {"fields": "status_code", "access_token": access_token})
        status = result.get("status_code")
        if status == "FINISHED":
            return
        if status == "ERROR":
            sys.exit(f"メディアコンテナの処理に失敗しました: {result}")
        time.sleep(3)


def publish(ig_user_id: str, creation_id: str, access_token: str) -> str:
    result = _post(
        f"{ig_user_id}/media_publish",
        {"creation_id": creation_id, "access_token": access_token},
    )
    if "id" not in result:
        sys.exit(f"公開に失敗しました: {result}")
    return result["id"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Instagram Graph APIで画像を投稿します")
    parser.add_argument("--image-url", required=True, help="投稿する画像の公開URL(raw.githubusercontent.com等)")
    parser.add_argument("--caption", required=True, help="投稿キャプション本文(ハッシュタグ込み)")
    parser.add_argument("--ig-user-id", default=os.environ.get("IG_USER_ID", ""), help="Instagramユーザー ID(/me で取得できるid)")
    parser.add_argument("--access-token", default=os.environ.get("IG_ACCESS_TOKEN", ""), help="Instagramアクセストークン(IGAA...)")
    args = parser.parse_args()

    if not args.ig_user_id:
        sys.exit("--ig-user-id または環境変数 IG_USER_ID を指定してください。")
    if not args.access_token:
        sys.exit("--access-token または環境変数 IG_ACCESS_TOKEN を指定してください。")

    container_id = create_container(args.ig_user_id, args.image_url, args.caption, args.access_token)
    wait_until_ready(container_id, args.access_token)
    media_id = publish(args.ig_user_id, container_id, args.access_token)
    print(media_id)


if __name__ == "__main__":
    main()
