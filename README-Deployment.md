# 🧩 FastAPI（Render）× Next.js（Vercel）デプロイ手順まとめ

このドキュメントは、**Render に FastAPI をデプロイ**し、  
**Vercel に Next.js をデプロイ**してフルスタックアプリを動かすための  
実際に動いた手順をまとめたものです。

---

# 📌 全体構成

```
ブラウザ
   ↓
Vercel（Next.js, frontend/）
   ↓ fetch()
Render（FastAPI, backend/）
```

- **フロント** → Vercel  
- **バックエンド** → Render  
- CORS と環境変数で両者を連携します。

---

# 🎯 1. FastAPI（backend）側の準備

## 1-1. CORS 設定（最重要）

`backend/main.py` に以下を追加します：

```python
import os
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost:3000",     # 開発環境（Next.js dev server）
    "http://127.0.0.1:3000",
]

# 本番の Vercel URL を環境変数で追加
frontend_origin = os.environ.get("FRONTEND_ORIGIN")
if frontend_origin:
    origins.append(frontend_origin)

app.add_middleware(
    CORSMiddleware(
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
)
```

---

# 🎯 2. backend を Render にデプロイ

Render で **Web Service** を作成します。

## 2-1. 設定

| 設定項目 | 値 |
|--------|-----|
| Root Directory | `backend` |
| Runtime | Python |
| Build Command | `pip install uv && uv sync` |
| Start Command | `uv run uvicorn main:app --host 0.0.0.0 --port $PORT` |

## 2-2. Render に設定する環境変数

```
FRONTEND_ORIGIN = https://your-vercel-app.vercel.app
```

（Vercel でデプロイ後の URL を設定）

## 2-3. 動作確認

ブラウザで：

```
https://your-backend.onrender.com/docs
```

が表示されれば OK。

---

# 🎯 3. Next.js（frontend）を Vercel にデプロイ

## 3-1. Vercel 設定

| 設定項目 | 値 |
|--------|-----|
| Root Directory | `frontend` |
| Framework Preset | Next.js（自動検出） |

## 3-2. Vercel の環境変数（API先）

```
NEXT_PUBLIC_API_BASE_URL = https://your-backend.onrender.com
```

## 3-3. Next.js コード側

`frontend/lib/api.ts` で API URL を参照：

```ts
const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
```

ローカルでは `localhost:8000`  
Vercel では Render の backend URL  
に自動で切り替わります。

---

# 🎯 4. フロントとバックの接続確認

1. Vercel URL にアクセス  
2. Assignment / Knapsack ページへ  
3. Solve を押す  
4. Render の FastAPI が返す結果が表示される

---

# 🎉 これで構成完成！

- **Next.js → Vercel** が最適  
- **FastAPI → Render** が安定  
- CORS と環境変数だけでスムーズに接続  
- 量子アニーリング系（OpenJij / Ocean）も Render なら問題なく動作

---

# 📎 補足：ローカル開発

```
cd backend
uv sync
mise run backend-dev
```

```
cd frontend
pnpm install
mise run frontend-dev
```
