# -*- coding: utf-8 -*-
"""Facebook長期アクセストークンの延長スクリプト(標準ライブラリのみ・pip不要)

長期トークンは発行から60日で失効する。失効前(24時間以上経過していればいつでも)に
このスクリプトを実行すると、新しい60日間有効なトークンを取得できる。

使い方:
    python refresh_token.py --app-id 123456 --app-secret xxxx --current-token EAAG...

出力された新しいトークンを、Claude Codeのスケジュールルーティン設定
(job_config内のプロンプト/環境変数)に手動で反映してください。
"""

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

API_VERSION = "v21.0"
BASE_URL = f"https://graph.facebook.com/{API_VERSION}"


def refresh(app_id: str, app_secret: str, current_token: str) -> dict:
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": current_token,
    }
    url = f"{BASE_URL}/oauth/access_token?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=30) as res:
            return json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        sys.exit(f"トークン延長に失敗しました (HTTP {e.code}):\n{detail}")


def main() -> None:
    parser = argparse.ArgumentParser(description="長期アクセストークンを新しい60日間トークンに延長します")
    parser.add_argument("--app-id", required=True, help="MetaアプリのApp ID")
    parser.add_argument("--app-secret", required=True, help="MetaアプリのApp Secret")
    parser.add_argument("--current-token", required=True, help="現在の(まだ失効していない)長期トークン")
    args = parser.parse_args()

    result = refresh(args.app_id, args.app_secret, args.current_token)
    if "access_token" not in result:
        sys.exit(f"予期しないレスポンス: {result}")

    print("新しいトークンが発行されました。ルーティン設定に反映してください:")
    print(result["access_token"])
    if "expires_in" in result:
        days = int(result["expires_in"]) // 86400
        print(f"(有効期限の目安: 約{days}日後)")


if __name__ == "__main__":
    main()
