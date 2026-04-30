#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------------------------
# deepseek-balance — 查询 DeepSeek API 账户余额
#
# 读取 ~/.claude/settings.json 获取当前模型配置和 API key。
# 仅当当前模型是 DeepSeek 时才执行查询，否则直接退出。
# ---------------------------------------------------------------------------

SETTINGS_FILE="$HOME/.claude/settings.json"

# ---------- 读取配置 ----------
if [[ ! -f "$SETTINGS_FILE" ]]; then
    echo "错误: 找不到 $SETTINGS_FILE"
    exit 1
fi

BASE_URL=$(jq -r '.env.ANTHROPIC_BASE_URL // empty' "$SETTINGS_FILE")
API_KEY=$(jq -r '.env.ANTHROPIC_AUTH_TOKEN // empty' "$SETTINGS_FILE")

if [[ -z "$BASE_URL" ]] || [[ -z "$API_KEY" ]]; then
    echo "错误: settings.json 中缺少 ANTHROPIC_BASE_URL 或 ANTHROPIC_AUTH_TOKEN"
    exit 1
fi

# ---------- 模型检查 ----------
if [[ "$BASE_URL" != *"deepseek"* ]]; then
    echo "当前模型不是 DeepSeek，无法查询 DeepSeek 余额。"
    echo "当前 BASE_URL: $BASE_URL"
    exit 0
fi

# ---------- 调用余额 API ----------
RESP=$(curl -s -w '\n%{http_code}' \
    -H "Authorization: Bearer ${API_KEY}" \
    -H "Accept: application/json" \
    "https://api.deepseek.com/user/balance")

HTTP_CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')

if [[ "$HTTP_CODE" != "200" ]]; then
    echo "API 请求失败 (HTTP $HTTP_CODE)"
    echo "$BODY"
    exit 1
fi

# ---------- 解析并展示 ----------
IS_AVAILABLE=$(echo "$BODY" | jq -r '.is_available')
CURRENCY=$(echo "$BODY" | jq -r '.balance_infos[0].currency // "N/A"')
TOTAL=$(echo "$BODY" | jq -r '.balance_infos[0].total_balance // "N/A"')
GRANTED=$(echo "$BODY" | jq -r '.balance_infos[0].granted_balance // "N/A"')
TOPPED=$(echo "$BODY" | jq -r '.balance_infos[0].topped_up_balance // "N/A"')

CURRENCY_SYMBOL="¥"
[[ "$CURRENCY" == "USD" ]] && CURRENCY_SYMBOL="$"

echo ""
echo "  DeepSeek 账户余额"
echo "  ──────────────────"
if [[ "$IS_AVAILABLE" == "true" ]]; then
    echo "  状态: ✅ 可用"
else
    echo "  状态: ⚠️  余额不足，请充值"
fi
echo ""
echo "  $CURRENCY:"
printf "    总余额:    %s%s\n" "$CURRENCY_SYMBOL" "$TOTAL"
printf "    充值余额:  %s%s\n" "$CURRENCY_SYMBOL" "$TOPPED"
printf "    赠送余额:  %s%s\n" "$CURRENCY_SYMBOL" "$GRANTED"
echo ""
