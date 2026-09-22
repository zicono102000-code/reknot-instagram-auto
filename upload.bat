@echo off
cd /d "%~dp0"
git add queue
git commit -m "Add queue photos"
git push
echo.
echo 完了しました。このウィンドウを閉じてください。
pause