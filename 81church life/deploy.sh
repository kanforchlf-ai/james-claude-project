#!/usr/bin/env bash
# 一鍵：跑週更新 → 推部署 repo（網站）→ 推備份 repo
set -euo pipefail

cd "$(dirname "$0")"

echo "=== 1/3 執行週更新腳本 ==="
TMP_LOG=$(mktemp)
python -X utf8 update_dashboard.py | tee "$TMP_LOG"

# 從輸出抓最新週次（例如「4月第三週」）
WEEK=$(grep -oE '最新資料週次：[0-9]+月第.週' "$TMP_LOG" | head -1 | sed 's/最新資料週次：//')
rm -f "$TMP_LOG"
[ -z "$WEEK" ] && WEEK="$(date +%Y-%m-%d)"
MSG="更新 $WEEK 出席資料"

echo
echo "=== 2/3 推部署 repo (kanforchlf-ai/81Y3-dashboard) → 網站 ==="
pushd 81Y3-dashboard > /dev/null
if [ -n "$(git status --porcelain)" ]; then
  git add -u
  git commit -m "$MSG"
  git push
  echo "✓ 部署 repo 已推送"
else
  echo "（無變更，跳過）"
fi
popd > /dev/null

echo
echo "=== 3/3 推備份 repo (jameskan-TW/james-claude-project) ==="
if [ -n "$(git status --porcelain 81Y3-dashboard)" ]; then
  git add 81Y3-dashboard
  git commit -m "$MSG"
  git push
  echo "✓ 備份 repo 已推送"
else
  echo "（無變更，跳過）"
fi

echo
echo "=== 完成 ==="
echo "網址：https://kanforchlf-ai.github.io/81Y3-dashboard/"
echo "（GitHub Pages 約 1-2 分鐘後更新）"
