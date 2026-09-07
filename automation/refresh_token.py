# -*- coding: utf-8 -*-
"""Instagramアクセストークンの延長スクリプト(標準ライブラリのみ・pip不要)

長期トークンは発行から約60日で失効する。失効前(発行から24時間以上経過していればいつでも)に
このスクリプトを実行すると、新しい約60日間有効なトークンを取得できる。

使い方:
    python refresh_token.py --current-token IGAA...

App Secretは不要(トークン自体だけで更新できる、Instagram API with Instagram Login方式の仕様)。

出力された新しいトークンを、Claude Codeのスケジュールルーティン設定
(job_config内のプロンプト/環境変数)に手動で反映してください。
"""

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "https://graph.instagram.com"


def refresh(current_token: str) -> dict:
    params = {
        "grant_type": "ig_refresh_token",
        "access_token": current_token,
    }
    url = f"{BASE_URL}/refresh_access_token?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=30) as res:
            return json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        sys.exit(f"トークン延長に失敗しました (HTTP {e.code}):\n{detail}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Instagramの長期アクセストークンを新しい約60日間トークンに延長します")
    parser.add_argument("--current-token", required=True, help="現在の(まだ失効していない)長期トークン")
    args = parser.parse_args()

    result = refresh(args.current_token)
    if "access_token" not in result:
        sys.exit(f"予期しないレスポンス: {result}")

    print("新しいトークンが発行されました。ルーティン設定に反映してください:")
    print(result["access_token"])
    if "expires_in" in result:
        days = int(result["expires_in"]) // 86400
        print(f"(有効期限の目安: 約{days}日後)")


if __name__ == "__main__":
    main()
