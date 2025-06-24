# セットアップガイド

LLM階層型ルール管理MCPサーバーのセットアップ手順を説明します。

## 📋 前提条件

- **Python 3.11以上** が必要です
- **Git** が利用可能である必要があります
- **仮想環境** の使用を強く推奨します

```bash
# Pythonバージョンの確認
python3 --version
```

## 🚀 自動セットアップ（推奨）

### 1. セットアップスクリプトの実行

```bash
# プロジェクトディレクトリに移動
cd /workspace/rules_mcp

# セットアップスクリプトの実行
chmod +x scripts/setup.sh
./scripts/setup.sh
```

セットアップスクリプトは以下を自動で行います：
- Python バージョンチェック
- 必要なディレクトリの作成
- 依存関係のインストール
- 環境設定ファイルの作成
- 基本動作テスト

### 2. Claude Code MCP設定

```bash
# Claude Code用の設定を生成
chmod +x setup_claude_mcp.sh
./setup_claude_mcp.sh
```

## 🔧 手動セットアップ

自動セットアップが失敗した場合の手動手順：

### 1. 仮想環境の作成

```bash
# 仮想環境の作成
python3 -m venv venv

# 仮想環境の有効化
source venv/bin/activate  # Linux/macOS
# または
venv\Scripts\activate     # Windows
```

### 2. 依存関係のインストール

```bash
# 依存関係のインストール
pip install -r requirements.txt

# または Poetry を使用
poetry install
```

### 3. 必要なディレクトリの作成

```bash
mkdir -p config/rules
mkdir -p logs
mkdir -p data
```

### 4. 環境設定ファイルの作成

```bash
# .env ファイルの作成
cp .env.example .env
```

必要に応じて `.env` ファイルを編集：

```bash
# 基本設定
FASTMCP_RULE_TRANSPORT=stdio
FASTMCP_RULE_RULES_DIR=config/rules
FASTMCP_RULE_LOG_LEVEL=INFO

# HTTPトランスポートを使用する場合
FASTMCP_RULE_TRANSPORT=streamable-http
FASTMCP_RULE_HOST=127.0.0.1
FASTMCP_RULE_PORT=8000
```

### 5. 動作確認

```bash
# 基本インポートテスト
PYTHONPATH=src python -c "from rule_manager.main import main; print('✅ Import successful')"

# ルール読み込みテスト
PYTHONPATH=src python -c "
import asyncio
from rule_manager.storage.yaml_store import YAMLRuleStore
from rule_manager.models.base import RuleScope

async def test():
    store = YAMLRuleStore('config/rules')
    ruleset = await store.load_rules(RuleScope.GLOBAL)
    print(f'✅ Loaded {len(ruleset.rules)} rules')

asyncio.run(test())
"

# ヘルプコマンドテスト
PYTHONPATH=src python -m rule_manager.main --help
```

## 🔗 Claude Code との連携設定

### MCP設定ファイル

Claude Code に以下の設定を追加：

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

### 設定手順

1. **設定ファイルの場所を確認**
   - `claude_mcp_config.json` ファイルが生成されています

2. **Claude Code への設定追加**
   - Claude Code の MCP 設定に上記の JSON を追加
   - または生成された設定ファイルの内容をコピー

3. **Claude Code の再起動**
   - 設定を反映するために Claude Code を再起動

## 🧪 動作テスト

### 基本機能テスト

```bash
# MCPサーバーの起動テスト
source venv/bin/activate
PYTHONPATH=src python -m rule_manager.main &
sleep 2
kill %1
```

### ルール評価テスト

```bash
# サンプルテストスクリプトの実行
source venv/bin/activate
PYTHONPATH=src python scripts/simple_test.py
```

### MCPツールテスト

```bash
# MCP機能のテスト
source venv/bin/activate
PYTHONPATH=src python scripts/test_working_mcp.py
```

## 📁 ディレクトリ構造

セットアップ後のディレクトリ構造：

```
rules_mcp/
├── config/
│   └── rules/              # ルール定義ファイル
│       ├── global.yaml     # グローバルルール
│       ├── project.yaml    # プロジェクトルール
│       └── individual.yaml # 個人ルール
├── data/                   # データファイル（SQLite等）
├── logs/                   # ログファイル
├── src/                    # ソースコード
│   └── rule_manager/
├── venv/                   # 仮想環境
├── .env                    # 環境設定
├── requirements.txt        # 依存関係
└── claude_mcp_config.json  # Claude Code設定
```

## 🛠️ トラブルシューティング

### よくある問題

#### 1. Python バージョンエラー
```bash
# 解決方法：Python 3.11以上を使用
python3 --version
```

#### 2. 依存関係エラー
```bash
# 解決方法：仮想環境内で再インストール
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### 3. PYTHONPATH エラー
```bash
# 解決方法：環境変数の設定
export PYTHONPATH=src
# または実行時に指定
PYTHONPATH=src python -m rule_manager.main
```

#### 4. ルールファイルが見つからない
```bash
# 解決方法：ルールディレクトリの確認
ls -la config/rules/
# サンプルルールが存在することを確認
```

#### 5. ポート使用中エラー（HTTPモード）
```bash
# 解決方法：別のポートを使用
PYTHONPATH=src python -m rule_manager.main --transport streamable-http --port 8081
```

### ログの確認

```bash
# デバッグモードでの実行
PYTHONPATH=src python -m rule_manager.main --log-level DEBUG

# ログファイルの確認
tail -f logs/audit.log  # 監査ログ
```

### 設定の確認

```bash
# 現在の設定の確認
PYTHONPATH=src python -c "
from rule_manager.models.settings import ServerSettings
settings = ServerSettings()
print(f'Transport: {settings.transport}')
print(f'Rules Dir: {settings.rules_dir}')
print(f'Storage Backend: {settings.storage_backend}')
"
```

## 📖 次のステップ

セットアップが完了したら：

1. **[QUICK_START.md](QUICK_START.md)** - 基本的な使い方
2. **[USAGE.md](USAGE.md)** - 詳細な利用方法
3. **[../CLAUDE.md](../CLAUDE.md)** - 開発者向けガイド

## 🔄 アップデート

```bash
# 最新のコードを取得
git pull origin main

# 依存関係の更新
source venv/bin/activate
pip install -r requirements.txt --upgrade

# 設定の再確認
./setup_claude_mcp.sh
```

## 🆘 サポート

問題が解決しない場合：

1. **ログの確認**: デバッグモードで詳細なログを確認
2. **設定の検証**: `.env` ファイルと実行環境を確認
3. **テストスクリプト**: `scripts/` ディレクトリのテストスクリプトを実行
4. **ドキュメント**: 他のドキュメントファイルを参照

---

**✅ セットアップが完了したら、Claude Code から rules_mcp サーバーに接続してルール管理機能をお試しください！**