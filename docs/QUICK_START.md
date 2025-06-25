# Quick Start Guide

## MCPサーバーの起動と動作確認

### 1. 依存関係のインストール

```bash
# 仮想環境の作成と有効化
python3 -m venv venv
source venv/bin/activate

# 依存関係のインストール
pip install -e .
```

### 2. サーバーの起動

```bash
# STDIO モード（デフォルト）
PYTHONPATH=src python -m rule_manager.main

# HTTP モード
PYTHONPATH=src python -m rule_manager.main --transport streamable-http --port 8080

# デバッグモード
PYTHONPATH=src python -m rule_manager.main --log-level DEBUG
```

### 3. 利用可能なMCPツール

以下のツールが利用可能です：

1. **evaluate_rules** - ルール評価の実行
2. **create_rule** - 新しいルールの作成
3. **update_rule** - 既存ルールの更新
4. **delete_rule** - ルールの削除
5. **list_rules** - ルール一覧の取得
6. **get_rule** - 特定ルールの取得
7. **validate_rule_dsl** - DSL式の検証
8. **health_check** - ヘルスチェック

### 4. Claude CodeへのMCP登録

```bash
# MCPサーバーをClaude Codeに追加
claude mcp add rules_mcp -e PYTHONPATH=src -- /workspace/rules_mcp/venv/bin/python -m rule_manager.main

# 登録確認
claude mcp list
# 出力: rules_mcp: /workspace/rules_mcp/venv/bin/python -m rule_manager.main
```

### 5. ルール評価の例

```python
# テストコンテキスト
context = {
    "user_id": "user123",
    "model_name": "gpt-4", 
    "prompt_length": 1500,
    "custom_attributes": {
        "user_role": "admin",
        "environment": "production"
    }
}

# 評価結果（実際の出力）
{
    "final_action": "allow",
    "matched_rules_count": 1,
    "applicable_rules_count": 11,
    "total_execution_time_ms": 8.45,
    "results": [...]
}
```

### 6. ルール設定ファイル

- `config/rules/global.yaml` - グローバルルール
- `config/rules/project.yaml` - プロジェクトルール
- `config/rules/individual.yaml` - 個人ルール

### 7. 環境設定

`.env` ファイルで設定をカスタマイズ：

```bash
FASTMCP_RULE_TRANSPORT=stdio
FASTMCP_RULE_RULES_DIR=config/rules
FASTMCP_RULE_LOG_LEVEL=INFO
```

## トラブルシューティング

### Pythonパスエラー
```bash
# 解決方法
PYTHONPATH=src python -m rule_manager.main
```

### ルールファイルが見つからない
```bash
# ルールディレクトリの確認
ls -la config/rules/
```

### ポート使用中エラー
```bash
# 別のポートを使用
python -m rule_manager.main --transport streamable-http --port 8081
```