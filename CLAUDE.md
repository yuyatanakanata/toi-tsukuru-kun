# 問いつくるくん - CLAUDE.md

## プロジェクト概要
思考実験展の「大問い」を生成するWebアプリ。
Flask + Groq API (llama-3.3-70b-versatile) + Render でデプロイ。

## 技術スタック
- **バックエンド**: Flask (Python 3.11)
- **AI API**: Groq API (`GROQ_API_KEY` 環境変数)
- **デプロイ**: Render (Docker, Free tier)
- **リポジトリ**: https://github.com/yuyatanakanata/toi-tsukuru-kun

## 開発ルール（これまでの学び）

### API・依存関係
- Gemini APIは使わない（nomore.jp組織ポリシーおよびアカウント問題で安定動作しない）
- Groq APIを使う。`groq==0.11.0` + `httpx<0.28.0` のバージョン固定必須（それ以外はproxiesエラーが出る）
- `GROQ_API_KEY` をRenderのEnvironment Variablesに設定する

### 言語・表記
- 「デジタル」と表記する（「ディジタル」は使わない）
- 出力はすべて自然な現代日本語

### 大問いの品質基準
- 「社会・政治的な正しさ」を問うものにしない
- 「〜することが正しいのか？」という形は避ける
- 両方に価値があるものが対立する構造にする（愛する人 vs 正義、など）
- 参加者が「自分ならどうする」と考える一人称の問いにする

## デプロイフロー
1. ローカルで変更
2. `git add . && git commit -m "..." && git push`
3. RenderがGitHub変更を検知して自動デプロイ（数分）
4. Renderの「Events」ページで「Deploy live」緑チェックを確認

## 作業ルール（Claude Codeへの指示）

### 複数ステップの変更はPlan Modeで先に整理する
- 3ステップ以上の変更は実装前にフローを書いてユーザーに確認する
- 途中でおかしくなったら立ち止まって再計画する

### 完了前に必ず確認する
- デプロイが必要な変更はRenderの「Deploy live」緑チェックまで確認を促す
- 動作確認をユーザーに求めてから完了とする

### Self-Improvement Loop
- ユーザーに修正を指摘されたら、同じミスをしないようCLAUDE.mdの「同じミスをしたら追記する」に記録する
- エラーが再発した場合は根本原因を調べてから直す（場当たり対応しない）

### Core Principles
- 変更は最小限に。要求されていない機能を勝手に追加しない
- 一時的な回避策より根本的な修正を優先する
- バグを報告されたらログ・エラー内容を確認してから直す

## 同じミスをしたら追記する
- Gemini APIは使わない（quota/組織ポリシーで動かない）→ Groqを使う
- `groq==0.11.0` + `httpx<0.28.0` の固定が必須（proxiesエラー対策）
- 「ディジタル」ではなく「デジタル」と書く
