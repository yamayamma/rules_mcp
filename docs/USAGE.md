# LLM Rule Manager MCP Server - 使い方ガイド

## 概要

このMCPサーバーは、LLMアプリケーション向けの階層型ルール管理システムです。グローバル、プロジェクト、個人レベルでルールを管理し、動的にルール評価を行います。

## インストールと設定

### 1. 依存関係のインストール

```bash
# 仮想環境の作成
python3 -m venv venv
source venv/bin/activate

# 開発モードでインストール
pip install -e .
```

### 2. 環境設定

```bash
# 環境設定ファイルをコピー
cp .env.example .env

# 必要に応じて設定を編集
vim .env
```

### 3. ルールディレクトリの準備

```bash
# ルールディレクトリが存在することを確認
ls -la config/rules/
```

## 起動方法

### STDIO トランスポート（デフォルト）

```bash
# 直接実行
PYTHONPATH=src python -m rule_manager.main

# 仮想環境から実行
venv/bin/python -m rule_manager.main
```

### HTTP トランスポート

```bash
# HTTPサーバーとして起動
PYTHONPATH=src python -m rule_manager.main --transport streamable-http --port 8080

# ホストとポートを指定
PYTHONPATH=src python -m rule_manager.main --transport streamable-http --host 0.0.0.0 --port 8080
```

### その他のオプション

```bash
# 詳細ログ
PYTHONPATH=src python -m rule_manager.main --log-level DEBUG

# カスタムルールディレクトリ
PYTHONPATH=src python -m rule_manager.main --rules-dir /path/to/custom/rules

# 環境ファイルを指定
PYTHONPATH=src python -m rule_manager.main --env-file .env.production

# 非同期モード（高並列）
PYTHONPATH=src python -m rule_manager.main --async-mode

# ヘルプ表示
PYTHONPATH=src python -m rule_manager.main --help
```

## MCP ツール一覧

### 1. `evaluate_rules`
ルールをコンテキストに対して評価します。

**パラメータ:**
```json
{
  "request": {
    "context": {
      "user_id": "user123",
      "project_id": "project456", 
      "model_name": "gpt-4",
      "prompt_length": 1500,
      "custom_attributes": {
        "user_role": "admin",
        "environment": "production"
      }
    }
  }
}
```

**レスポンス:**
```json
{
  "context": {...},
  "results": [
    {
      "rule_name": "allow_admins",
      "action": "allow",
      "matched": true,
      "priority": 90,
      "execution_time_ms": 15.2
    }
  ],
  "final_action": "allow",
  "total_execution_time_ms": 25.7,
  "evaluated_at": "2025-01-20T12:00:00Z",
  "applicable_rules_count": 11,
  "matched_rules_count": 1
}
```

### 2. `create_rule`
新しいルールを作成します。

**パラメータ:**
```json
{
  "request": {
    "name": "new_security_rule",
    "scope": "global",
    "priority": 85,
    "action": "deny",
    "conditions": {
      "security_check": "user_clearance_level < 3"
    },
    "parameters": {
      "error_message": "Insufficient security clearance"
    },
    "description": "Security clearance rule",
    "enabled": true
  }
}
```

### 3. `update_rule`
既存のルールを更新します。

**パラメータ:**
```json
{
  "request": {
    "name": "existing_rule_name",
    "scope": "global",
    "priority": 90,
    "description": "Updated description"
  }
}
```

### 4. `delete_rule`
ルールを削除します。

**パラメータ:**
- `rule_name`: 削除するルール名
- `scope`: ルールのスコープ

### 5. `list_rules`
ルール一覧を取得します。

**パラメータ:**
- `scope` (オプション): 特定のスコープでフィルタ

### 6. `get_rule`
特定のルールを取得します。

**パラメータ:**
- `rule_name`: ルール名
- `scope` (オプション): スコープ

### 7. `validate_rule_dsl`
DSL式を検証します。

**パラメータ:**
- `expression`: 検証するDSL式

### 8. `health_check`
サーバーの健康状態を確認します。

## DSL 記法ガイド

### 基本比較演算子
```yaml
conditions:
  user_check: 'user_id == "user123"'
  numeric_check: 'prompt_length > 1000'
  list_check: 'model_name in ["gpt-4", "claude"]'
  string_check: 'user_id startswith "admin"'
```

### 論理演算子
```yaml
conditions:
  complex_and: 'user_id == "admin" and environment == "production"'
  complex_or: 'user_role == "admin" or user_clearance_level >= 5'
  negation: 'not user_suspended == true'
```

### コンテキスト変数アクセス
```yaml
conditions:
  # 直接属性
  direct: 'user_id == "test"'
  
  # カスタム属性
  custom: 'custom_attributes.user_role == "admin"'
  
  # ネストした属性（省略記法）
  nested: 'user_role == "admin"'
```

### データ型
```yaml
conditions:
  string: 'name == "value"'
  number: 'count > 100'
  boolean: 'enabled == true'
  null: 'optional_field == null'
  list: 'item in ["a", "b", "c"]'
```

## 設定例

### .env ファイル
```bash
# トランスポート設定
FASTMCP_RULE_TRANSPORT=stdio
FASTMCP_RULE_HOST=127.0.0.1
FASTMCP_RULE_PORT=8000

# ストレージ設定
FASTMCP_RULE_STORAGE_BACKEND=yaml
FASTMCP_RULE_RULES_DIR=config/rules

# セキュリティ設定
FASTMCP_RULE_ENABLE_AUTH=false

# ログ設定
FASTMCP_RULE_LOG_LEVEL=INFO
FASTMCP_RULE_LOG_FORMAT=json
```

### ルールファイル例 (global.yaml)
```yaml
ruleset_version: "1.1"
engine_min_version: ">=2.8.0"
scope: global
rules:
  - name: "admin_access"
    scope: global
    priority: 90
    action: allow
    conditions:
      role_check: 'user_role == "admin"'
    parameters:
      message: "Admin access granted"
    
  - name: "rate_limit"
    scope: global  
    priority: 80
    action: deny
    conditions:
      rate_check: 'request_count_per_minute > 100'
    parameters:
      error_message: "Rate limit exceeded"
      retry_after_seconds: 60
```

## トラブルシューティング

### よくあるエラー

1. **StorageLockError (E201)**
   - 原因: ファイルロックの競合
   - 解決: しばらく待ってから再試行

2. **RuleDSLSyntaxError (E001)**
   - 原因: DSL記法エラー
   - 解決: `validate_rule_dsl` ツールで記法を確認

3. **RuleNotFoundError (E003)**
   - 原因: 存在しないルールの操作
   - 解決: `list_rules` でルール一覧を確認

### ログ確認

```bash
# ログレベルを上げて詳細情報を確認
PYTHONPATH=src python -m rule_manager.main --log-level DEBUG

# 特定のディレクトリでログファイルを確認
tail -f logs/audit.db
```

### パフォーマンス調整

```bash
# 高並列処理
PYTHONPATH=src python -m rule_manager.main --async-mode --max-concurrent-evaluations 200

# キャッシュサイズ調整
FASTMCP_RULE_CACHE_SIZE_MB=128 PYTHONPATH=src python -m rule_manager.main
```

## 開発・テスト

### 単体テスト実行
```bash
source venv/bin/activate
pytest tests/unit/
```

### 統合テスト実行
```bash
source venv/bin/activate
pytest tests/integration/
```

### 負荷テスト実行
```bash
source venv/bin/activate
locust -f tests/load/
```