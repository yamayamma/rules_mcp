# MCPサーバーセットアップガイド

LLM階層型ルール管理MCPサーバーをClaude Codeに統合するための完全なセットアップガイドです。

## 📋 前提条件

- Python 3.11以上
- Claude Code CLI
- Git（オプション）

## 🚀 クイックセットアップ

### 1. 環境の準備

```bash
# プロジェクトディレクトリに移動
cd /workspace/rules_mcp

# Python仮想環境の作成
python3 -m venv venv

# 仮想環境のアクティベート
source venv/bin/activate

# 依存関係のインストール
pip install -e .
```

### 2. Claude CodeへのMCPサーバー追加

```bash
# MCPサーバーをClaude Codeに登録
claude mcp add rules_mcp -e PYTHONPATH=src -- /workspace/rules_mcp/venv/bin/python -m rule_manager.main
```

### 3. 動作確認

```bash
# 登録されたMCPサーバーの確認
claude mcp list

# 出力例:
# rules_mcp: /workspace/rules_mcp/venv/bin/python -m rule_manager.main
```

### 4. Claude Codeの再起動

MCPサーバーを認識させるため、Claude Codeを再起動してください。

## 🔧 詳細セットアップ

### プロジェクトレベル設定

プロジェクト内の他の開発者と設定を共有したい場合は、`.mcp.json`ファイルを作成します：

```json
{
  "mcpServers": {
    "rules_mcp": {
      "command": "/workspace/rules_mcp/venv/bin/python",
      "args": ["-m", "rule_manager.main"],
      "env": {
        "PYTHONPATH": "src"
      }
    }
  }
}
```

### 環境変数の設定

`.env`ファイルを作成してサーバー設定をカスタマイズできます：

```bash
# .env ファイルの作成
cp .env.example .env

# 設定の編集（必要に応じて）
# FASTMCP_RULE_TRANSPORT=stdio
# FASTMCP_RULE_LOG_LEVEL=INFO
# FASTMCP_RULE_STORAGE_BACKEND=yaml
```

## ✅ 動作テスト

### 1. サーバーの直接起動テスト

```bash
# STDIOモードでのテスト起動
PYTHONPATH=src venv/bin/python -m rule_manager.main --help

# 出力にヘルプメッセージが表示されれば成功
```

### 2. ルールエンジンのテスト

```bash
# Python対話モードでのテスト
PYTHONPATH=src venv/bin/python -c "
import asyncio
from rule_manager.storage.yaml_store import YAMLRuleStore
from rule_manager.core.engine import RuleEngine
from rule_manager.models.base import RuleContext

async def test():
    store = YAMLRuleStore('config/rules')
    engine = RuleEngine(store)
    
    context = RuleContext(
        user_id='test_user',
        model_name='gpt-4',
        prompt_length=1000,
        custom_attributes={'user_role': 'admin'}
    )
    
    result = await engine.evaluate_rules(context)
    print(f'動作テスト成功: {result.final_action}')
    print(f'評価時間: {result.total_execution_time_ms:.2f}ms')
    print(f'適用ルール数: {result.applicable_rules_count}')

asyncio.run(test())
"
```

期待される出力例：
```
動作テスト成功: RuleAction.ALLOW
評価時間: 5.23ms
適用ルール数: 17
```

### 3. MCPツールの利用確認

Claude Code内で以下のツールが利用可能になります：

| ツール名 | 機能 |
|---------|------|
| `evaluate_rules` | ルールコンテキストの評価 |
| `create_rule` | 新しいルールの作成 |
| `update_rule` | 既存ルールの更新 |
| `delete_rule` | ルールの削除 |
| `list_rules` | ルール一覧の取得 |
| `get_rule` | 特定ルールの取得 |
| `validate_rule_dsl` | DSL式の検証 |
| `health_check` | ヘルスチェック |

## 🎯 使用例

### 基本的なルール評価

```python
# Claude Code内でのMCPツール使用例
evaluate_rules({
  "context": {
    "user_id": "user123",
    "model_name": "gpt-4", 
    "prompt_length": 1500,
    "custom_attributes": {
      "environment": "production",
      "user_role": "admin"
    }
  }
})
```

### 新しいルールの作成

```python
create_rule({
  "name": "my_custom_rule",
  "scope": "individual",
  "priority": 60,
  "action": "modify",
  "conditions": {
    "model_preference": "model_name.startswith('claude')"
  },
  "parameters": {
    "preferred_model": "claude-3-sonnet"
  },
  "description": "Redirect to Claude models"
})
```

## 🔧 トラブルシューティング

### よくある問題と解決方法

#### 1. MCPサーバーが認識されない

**症状**: `claude mcp list`でサーバーが表示されない

**解決方法**:
```bash
# MCPサーバーを削除して再追加
claude mcp remove rules_mcp
claude mcp add rules_mcp -e PYTHONPATH=src -- /workspace/rules_mcp/venv/bin/python -m rule_manager.main
```

#### 2. Python依存関係エラー

**症状**: `ModuleNotFoundError`や`ImportError`

**解決方法**:
```bash
# 仮想環境の再作成
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

#### 3. ルールファイルが見つからない

**症状**: `config/rules`ディレクトリのエラー

**解決方法**:
```bash
# ルールディレクトリの作成
mkdir -p config/rules

# サンプルルールファイルが存在することを確認
ls -la config/rules/
```

#### 4. 権限エラー

**症状**: ファイルロックやアクセスエラー

**解決方法**:
```bash
# 権限の修正
chmod 755 config/rules/
chmod 644 config/rules/*.yaml
```

### ログの確認方法

```bash
# デバッグモードでの起動
PYTHONPATH=src venv/bin/python -m rule_manager.main --log-level DEBUG --verbose

# または環境変数での設定
export FASTMCP_RULE_LOG_LEVEL=DEBUG
PYTHONPATH=src venv/bin/python -m rule_manager.main
```

## 📊 パフォーマンス監視

### ヘルスチェック

```python
# Claude Code内でのヘルスチェック
health_check()

# 期待される出力:
# {
#   "success": true,
#   "healthy": true,
#   "storage_backend": "yaml",
#   "timestamp": "2025-06-24T23:51:24Z"
# }
```

### 評価パフォーマンス

- **目標応答時間**: < 100ms (p95)
- **同時接続数**: 100セッション対応
- **メモリ使用量**: < 256MB

## 🔄 アップデート手順

```bash
# 最新コードの取得（Gitを使用している場合）
git pull origin main

# 依存関係の更新
source venv/bin/activate
pip install -e . --upgrade

# MCPサーバーの再登録（必要に応じて）
claude mcp remove rules_mcp
claude mcp add rules_mcp -e PYTHONPATH=src -- /workspace/rules_mcp/venv/bin/python -m rule_manager.main
```

## 🎉 完了チェックリスト

- [ ] Python仮想環境の作成・アクティベート
- [ ] 依存関係のインストール完了
- [ ] MCPサーバーのClaude Codeへの追加
- [ ] `claude mcp list`での確認
- [ ] Claude Codeの再起動
- [ ] ルールエンジンの動作テスト成功
- [ ] MCPツールの利用確認
- [ ] サンプルルール評価の実行

すべてのチェックが完了すれば、LLM階層型ルール管理MCPサーバーが正常に動作しています！

---

## 🆘 サポート

問題が発生した場合は、以下の情報を含めてイシューを報告してください：

1. 実行環境（OS、Pythonバージョン）
2. エラーメッセージの詳細
3. 実行したコマンド
4. `claude mcp list`の出力
5. ログの内容（`--log-level DEBUG`で取得）

**💡 このガイドに従って、rules_mcpサーバーを簡単にClaude Codeに統合できます。**