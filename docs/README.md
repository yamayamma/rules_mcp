# ドキュメント

LLM階層型ルール管理MCPサーバーのドキュメント一覧です。

## 📚 ドキュメント構成

### 🚀 セットアップ・導入

- **[SETUP.md](SETUP.md)** - 詳細なセットアップ手順
  - 自動セットアップスクリプト
  - 手動セットアップ手順
  - Claude Code との連携設定
  - トラブルシューティング

- **[QUICK_START.md](QUICK_START.md)** - クイックスタートガイド
  - 基本的な起動手順
  - 利用可能なMCPツール
  - 動作テスト方法
  - 簡単な使用例

### 🔌 統合・活用

- **[MCP_INTEGRATION.md](MCP_INTEGRATION.md)** - MCP統合ガイド
  - Claude Code との統合
  - その他MCPクライアントとの統合
  - 全MCPツールの詳細仕様
  - 実際の使用例とワークフロー

- **[USAGE.md](USAGE.md)** - 詳細な利用方法
  - ルール作成・管理
  - DSL記法の詳細
  - 高度な設定オプション
  - 実践的な活用例

## 🔍 目的別ガイド

### 初めて使用する場合
1. **[SETUP.md](SETUP.md)** でセットアップ
2. **[QUICK_START.md](QUICK_START.md)** で基本動作確認
3. **[MCP_INTEGRATION.md](MCP_INTEGRATION.md)** でClaude Code連携

### 詳細な機能を知りたい場合
1. **[USAGE.md](USAGE.md)** で全機能を確認
2. **[MCP_INTEGRATION.md](MCP_INTEGRATION.md)** でAPI仕様確認
3. **[../CLAUDE.md](../CLAUDE.md)** で開発者情報確認

### 問題解決が必要な場合
1. **[SETUP.md](SETUP.md)** のトラブルシューティング
2. **[QUICK_START.md](QUICK_START.md)** の動作テスト
3. **[MCP_INTEGRATION.md](MCP_INTEGRATION.md)** のデバッグ情報

## 📖 その他のリソース

### プロジェクトルート
- **[../README.md](../README.md)** - プロジェクト概要（日本語）
- **[../CLAUDE.md](../CLAUDE.md)** - 開発者向けガイド

### 設定ファイル
- **[../.env.example](../.env.example)** - 環境設定の例
- **[../config/rules/](../config/rules/)** - サンプルルールファイル

### スクリプト
- **[../scripts/](../scripts/)** - セットアップ・テストスクリプト

## 🆘 サポート

### よくある質問

**Q: セットアップがうまくいかない**
→ [SETUP.md](SETUP.md) のトラブルシューティングセクションを確認

**Q: Claude Code で接続できない**
→ [MCP_INTEGRATION.md](MCP_INTEGRATION.md) の統合手順を確認

**Q: ルールの書き方がわからない**
→ [USAGE.md](USAGE.md) のルール作成セクションを確認

**Q: MCPツールの使い方がわからない**
→ [MCP_INTEGRATION.md](MCP_INTEGRATION.md) のツール仕様を確認

### デバッグ手順

1. **基本動作確認**
   ```bash
   PYTHONPATH=src python -m rule_manager.main --help
   ```

2. **ルール読み込み確認**
   ```bash
   PYTHONPATH=src python scripts/simple_test.py
   ```

3. **MCP接続確認**
   ```bash
   PYTHONPATH=src python scripts/test_working_mcp.py
   ```

---

**💡 各ドキュメントは段階的に読み進めることで、rules_mcpサーバーを効果的に活用できるように構成されています。**