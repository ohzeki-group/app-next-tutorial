# 🚀 Quantum Annealing Web App（Next.js + FastAPI）セットアップ手順

このプロジェクトは **WSL2（Windows） + mise + pnpm + uv** を前提として動作確認を行っています。  
macOS / Linux でも同じ手順で動作します。

---

# 🖥️ 事前準備（PreInstall）

## 🔳 Windows ユーザーへ（強く推奨：WSL2 を使用してください）

WSL2 のインストール：

```powershell
wsl --install
```

インストール後、Ubuntu などのディストリビューションをセットアップしてください。

🔗 Microsoft公式: https://learn.microsoft.com/ja-jp/windows/wsl/install

---

## 🔧 共通：mise のインストール

**mise（ランタイム管理ツール）**を使用して  
Node / pnpm / uv / Python などのバージョン管理を行います。

インストール方法はこちら：

🔗 https://mise.jdx.dev/getting-started.html

macOS / Linux なら：

```bash
curl https://mise.jdx.dev/install.sh | sh
```

Windows + WSL2 でも同じコマンドで導入できます。

---

# 📦 プロジェクトのインストール手順

以下は WSL2 / macOS / Linux のシェルで作業してください。

プロジェクトルートへ移動したら：

---

## 1. mise.toml を信頼（trust）

```bash
mise trust
```

---

## 2. ランタイムのインストール

```bash
mise install
```

これにより：

- Node.js
- pnpm
- uv（Python ランタイム＋パッケージ管理）

などが自動的にセットアップされます。

---

## 3. backend の依存関係インストール（uv）

```bash
cd backend
uv sync
```

---

## 4. frontend の依存関係インストール（pnpm）

```bash
cd frontend
pnpm install
```

---

# ▶️ ローカル実行（docker を使わない場合）

`mise.toml` に task を定義しているので、コマンドはとてもシンプルです。

---

## 🔥 Backend（FastAPI）を起動

```bash
mise run backend-dev
```

内部では次のコマンドが実行されています：

```bash
cd backend
uv run uvicorn main:app --reload --port 8000
```

- http://localhost:8000/docs → API ドキュメントが確認できます  
- `--reload` によりコード変更時に即ホットリロードされます

---

## ⚡ Frontend（Next.js）を起動

```bash
mise run frontend-dev
```

内部では次のコマンドが実行されています：

```bash
cd frontend
pnpm dev
```

- http://localhost:3000 にアクセス  
- UI 側は自動リロード（HMR）に対応します  

---

# 🌐 確認

1. ブラウザで http://localhost:3000 を開く  
2. Assignment / Knapsack ページへ移動  
3. Solve ボタンで FastAPI にリクエスト → 量子アニーリングの最適化結果が表示されれば成功 🎉

---

# 📎 補足

- Windows 上で直接 FastAPI / Next.js を走らせるより、  
  **WSL2 上で動かした方が高速・安定**です  
- Python / Node のバージョンはすべて **mise** が管理するため、  
  他プロジェクトとの衝突を避けられます  
- 必要なら `docker-compose` による統合環境構築も可能  

---
