# MCP統合ガイド

LLM階層型ルール管理MCPサーバーをClaude Codeやその他のMCPクライアントと統合する方法を説明します。

## 🔌 MCPクライアント統合

### Claude Code との統合

#### 1. MCP設定ファイルの作成

Claude Code の設定ディレクトリに以下の設定を追加：

```json
{
  "mcpServers": {
    "rules_mcp": {
      "command": "/workspace/rules_mcp/venv/bin/python",
      "args": ["-m", "rule_manager.main"],
      "cwd": "/workspace/rules_mcp",
      "env": {
        "PYTHONPATH": "src"
      }
    }
  }
}
```

#### 2. 自動設定スクリプト

プロジェクトに含まれるセットアップスクリプトを使用：

```bash
cd /workspace/rules_mcp
./setup_claude_mcp.sh
```

生成された `claude_mcp_config.json` の内容をClaude Codeの設定にコピーしてください。

### その他のMCPクライアント

#### Node.js MCPクライアント

```javascript
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const transport = new StdioClientTransport({
  command: "/workspace/rules_mcp/venv/bin/python",
  args: ["-m", "rule_manager.main"],
  cwd: "/workspace/rules_mcp",
  env: { ...process.env, PYTHONPATH: "src" }
});

const client = new Client({
  name: "rules-mcp-client",
  version: "1.0.0"
}, {
  capabilities: {}
});

await client.connect(transport);
```

#### Python MCPクライアント

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(
        command="/workspace/rules_mcp/venv/bin/python",
        args=["-m", "rule_manager.main"],
        cwd="/workspace/rules_mcp",
        env={"PYTHONPATH": "src"}
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # ツールの使用例
            result = await session.call_tool("health_check", {})
            print(result)

asyncio.run(main())
```

## 🛠️ 利用可能なMCPツール

### 1. evaluate_rules

ルールコンテキストに対してルール評価を実行します。

**パラメータ:**
```json
{
  "context": {
    "user_id": "string",
    "project_id": "string", 
    "model_name": "string",
    "prompt_length": "number",
    "custom_attributes": {
      "environment": "string",
      "user_role": "string"
    }
  }
}
```

**レスポンス例:**
```json
{
  "context": {...},
  "results": [
    {
      "rule_name": "rate_limit_check",
      "action": "deny",
      "matched": false,
      "priority": 90,
      "execution_time_ms": 2.5
    }
  ],
  "final_action": "allow",
  "total_execution_time_ms": 15.2,
  "matched_rules_count": 1
}
```

### 2. create_rule

新しいルールを作成します。

**パラメータ:**
```json
{
  "name": "my_custom_rule",
  "scope": "global",
  "priority": 50,
  "action": "allow",
  "conditions": {
    "user_role": "user_role == 'admin'"
  },
  "parameters": {
    "message": "Admin access granted"
  },
  "description": "Allow admin users"
}
```

### 3. update_rule

既存のルールを更新します。

**パラメータ:**
```json
{
  "name": "existing_rule",
  "scope": "global",
  "priority": 60,
  "enabled": false
}
```

### 4. delete_rule

ルールを削除します。

**パラメータ:**
```json
{
  "rule_name": "rule_to_delete",
  "scope": "global"
}
```

### 5. list_rules

ルール一覧を取得します。

**パラメータ (オプション):**
```json
{
  "scope": "global"  // 省略時は全スコープ
}
```

**レスポンス:**
```json
{
  "success": true,
  "rules": [...],
  "count": 5
}
```

### 6. get_rule

特定のルールを取得します。

**パラメータ:**
```json
{
  "rule_name": "specific_rule",
  "scope": "global"  // オプション
}
```

### 7. validate_rule_dsl

DSL式の検証を行います。

**パラメータ:**
```json
{
  "expression": "user_id == 'admin' and prompt_length > 1000"
}
```

**レスポンス:**
```json
{
  "success": true,
  "valid": true,
  "issues": []
}
```

### 8. health_check

サーバーのヘルスチェックを実行します。

**パラメータ:** なし

**レスポンス:**
```json
{
  "success": true,
  "healthy": true,
  "storage_backend": "yaml",
  "timestamp": "2025-01-20T10:30:00Z"
}
```

## 🔧 トランスポート設定

### STDIO (デフォルト)

最も一般的で、Claude Codeで推奨されるトランスポート：

```bash
PYTHONPATH=src python -m rule_manager.main
```

### Streamable HTTP

Webベースのクライアント向け：

```bash
PYTHONPATH=src python -m rule_manager.main --transport streamable-http --port 8080
```

### SSE (Server-Sent Events)

レガシークライアント向け：

```bash
PYTHONPATH=src python -m rule_manager.main --transport sse --port 8080
```

## 🎯 実際の使用例

### Claude Code での使用例

```typescript
// ルール評価の実行
const result = await mcp.callTool("evaluate_rules", {
  context: {
    user_id: "user123",
    model_name: "gpt-4",
    prompt_length: 1500,
    custom_attributes: {
      environment: "production",
      user_role: "standard"
    }
  }
});

// 新しいルールの作成
await mcp.callTool("create_rule", {
  name: "production_safety",
  scope: "project",
  priority: 85,
  action: "validate",
  conditions: {
    environment: "environment == 'production'"
  },
  parameters: {
    require_approval: true
  }
});
```

### カスタムワークフローの例

```python
async def evaluate_and_create_rule(client, context):
    # 1. 現在のルール評価
    evaluation = await client.call_tool("evaluate_rules", {
        "context": context
    })
    
    # 2. 結果に基づいた新ルール作成
    if evaluation["final_action"] == "deny":
        await client.call_tool("create_rule", {
            "name": f"auto_rule_{context['user_id']}",
            "scope": "individual",
            "action": "allow",
            "conditions": {
                "user_exception": f"user_id == '{context['user_id']}'"
            }
        })
```

## 📊 監視とデバッグ

### ログレベルの設定

```bash
# デバッグモード
PYTHONPATH=src python -m rule_manager.main --log-level DEBUG

# 本番環境
PYTHONPATH=src python -m rule_manager.main --log-level INFO
```

### ヘルスチェックの監視

```bash
# 定期的なヘルスチェック
while true; do
  echo "Health check at $(date)"
  curl -X POST http://localhost:8080/health_check || break
  sleep 60
done
```

### メトリクスの取得

```bash
# Prometheusメトリクス (有効時)
curl http://localhost:9090/metrics
```

## 🔒 セキュリティ考慮事項

### 認証の有効化

```bash
# JWTトークン認証の有効化
export FASTMCP_RULE_ENABLE_AUTH=true
export FASTMCP_RULE_JWT_SECRET_KEY="your-secret-key-here"
PYTHONPATH=src python -m rule_manager.main
```

### アクセス制御

```python
# クライアント側でのトークン設定
headers = {
    "Authorization": "Bearer your-jwt-token"
}
```

### 監査ログ

```bash
# 監査ログの確認
tail -f logs/audit.db
```

## 🚀 パフォーマンス最適化

### 並行処理の有効化

```bash
# 高並行処理モード
PYTHONPATH=src python -m rule_manager.main --async-mode
```

### キャッシュ設定

```bash
# キャッシュサイズの調整
export FASTMCP_RULE_CACHE_SIZE_MB=128
```

### 接続プール

```python
# クライアント側での接続プール設定
client_pool = MCPClientPool(
    max_connections=10,
    server_config=server_params
)
```

## 🔧 トラブルシューティング

### 接続エラー

```bash
# サーバーの状態確認
ps aux | grep rule_manager
netstat -tlnp | grep 8080
```

### タイムアウトエラー

```bash
# タイムアウト設定の調整
export FASTMCP_RULE_MAX_EVALUATION_TIME_MS=5000
```

### メモリ使用量

```bash
# メモリ使用量の監視
top -p $(pgrep -f rule_manager)
```

---

**💡 MCP統合により、rules_mcpサーバーを様々なLLMアプリケーションワークフローに組み込むことができます。**