# -*- coding: utf-8 -*-
"""queue内でキャプションが揃っている最も古い画像を1件だけInstagramに投稿する。

GitHub Actions(.github/workflows/auto-post.yml)から実行される想定。
このリポジトリを直接cloneしているClaude Codeのクラウド環境は
graph.instagram.comへのアウトバウンド接続が組織ポリシーでブロックされているため、
実際の投稿処理はGitHub Actionsランナー側に分離している。

前提:
    各画像ファイル(queue/xxx.jpg 等)に対して、同じ名前+".caption.txt"の
    テキストファイル(queue/xxx.jpg.caption.txt)がキャプション本文として
    用意されていること。キャプションファイルが無い画像はまだ準備中とみなし、
    スキップする(エラーにはしない)。

処理の流れ:
    1. queue/ 内の画像をファイル名昇順に並べ、キャプションファイルが
       揃っている最初の1件を選ぶ。無ければ何もせず終了。
    2. raw.githubusercontent.com の公開URLを組み立てる。
    3. post_to_instagram.py のロジック(コンテナ作成→待機→公開)を再利用して投稿する。
    4. 成功したら画像をposted/へ移動し、キャプションファイルを削除し、
       log/history.jsonに記録し、commit・pushする。
    5. 失敗した場合は何もcommitせず終了する(次回実行時に自動的にリトライされる)。

アクセストークンは環境変数からのみ読み込み、いかなるファイルにも書き込まない。
"""

import json
import os
import subprocess
import sys
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from post_to_instagram import create_container, publish, wait_until_ready  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
QUEUE_DIR = REPO_ROOT / "queue"
POSTED_DIR = REPO_ROOT / "posted"
HISTORY_PATH = REPO_ROOT / "log" / "history.json"
IMAGE_EXTS = {".jpg", ".jpeg", ".png"}


def find_next_post():
    images = sorted(
        p for p in QUEUE_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    )
    for image_path in images:
        caption_path = image_path.with_name(image_path.name + ".caption.txt")
        if caption_path.exists():
            return image_path, caption_path
    return None, None


def build_image_url(image_path: Path) -> str:
    repo_slug = os.environ["GITHUB_REPOSITORY"]
    branch = os.environ.get("GITHUB_REF_NAME", "master")
    encoded_name = urllib.parse.quote(image_path.name)
    return f"https://raw.githubusercontent.com/{repo_slug}/{branch}/queue/{encoded_name}"


def run_git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, cwd=REPO_ROOT)


def main() -> None:
    ig_user_id = os.environ.get("IG_USER_ID", "")
    access_token = os.environ.get("IG_ACCESS_TOKEN", "")
    if not ig_user_id or not access_token:
        sys.exit("環境変数 IG_USER_ID / IG_ACCESS_TOKEN が設定されていません。")

    image_path, caption_path = find_next_post()
    if image_path is None:
        print("投稿待ち(キャプション準備済み)の画像はありません。")
        return

    caption = caption_path.read_text(encoding="utf-8").strip()
    image_url = build_image_url(image_path)

    print(f"投稿対象: {image_path.name}")
    container_id = create_container(ig_user_id, image_url, caption, access_token)
    wait_until_ready(container_id, access_token)
    media_id = publish(ig_user_id, container_id, access_token)
    print(f"投稿成功: media_id={media_id}")

    posted_path = POSTED_DIR / image_path.name
    image_path.rename(posted_path)
    caption_path.unlink()

    history = json.loads(HISTORY_PATH.read_text(encoding="utf-8")) if HISTORY_PATH.exists() else []
    history.append({
        "media_id": media_id,
        "file": f"posted/{image_path.name}",
        "posted_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+0000"),
        "caption": caption,
    })
    HISTORY_PATH.write_text(json.dumps(history, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    run_git("config", "user.name", "reknot-auto-poster")
    run_git("config", "user.email", "actions@users.noreply.github.com")
    run_git("add", "-A", "--", "queue", "posted", "log/history.json")
    run_git("commit", "-m", f"Auto-post: {image_path.name}")
    run_git("push")


if __name__ == "__main__":
    main()
