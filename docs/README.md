# ドキュメント

LLM階層型ルール管理MCPサーバーのドキュメント一覧です。

## 📚 ドキュメント構成

### 🚀 セットアップ・導入

- **[MCP_SETUP_GUIDE.md](MCP_SETUP_GUIDE.md)** - 完全セットアップガイド
  - Python環境の準備
  - Claude CodeへのMCP登録
  - 動作テスト・確認方法
  - トラブルシューティング

- **[QUICK_START.md](QUICK_START.md)** - クイックスタートガイド
  - 基本的な起動手順
  - Claude CodeのMCP登録
  - 利用可能なMCPツール
  - 簡単な使用例

- **[WORKING_STATUS.md](WORKING_STATUS.md)** - 現在の動作状況
  - 完了した実装と設定
  - 登録済みルール (11個) の詳細
  - パフォーマンス実績
  - 利用可能なMCPツール状況

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
1. **[MCP_SETUP_GUIDE.md](MCP_SETUP_GUIDE.md)** でセットアップ
2. **[QUICK_START.md](QUICK_START.md)** で基本動作確認
3. **[WORKING_STATUS.md](WORKING_STATUS.md)** で現在の状況確認
4. **[MCP_INTEGRATION.md](MCP_INTEGRATION.md)** でClaude Code連携

### 詳細な機能を知りたい場合
1. **[USAGE.md](USAGE.md)** で全機能を確認
2. **[MCP_INTEGRATION.md](MCP_INTEGRATION.md)** でAPI仕様確認
3. **[../CLAUDE.md](../CLAUDE.md)** で開発者情報確認

### 問題解決が必要な場合
1. **[WORKING_STATUS.md](WORKING_STATUS.md)** で動作状況確認
2. **[MCP_SETUP_GUIDE.md](MCP_SETUP_GUIDE.md)** のトラブルシューティング
3. **[QUICK_START.md](QUICK_START.md)** の動作テスト
4. **[MCP_INTEGRATION.md](MCP_INTEGRATION.md)** のデバッグ情報

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
→ [MCP_SETUP_GUIDE.md](MCP_SETUP_GUIDE.md) のトラブルシューティングセクションを確認

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