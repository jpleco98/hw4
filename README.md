# Campus Customs: Yale apparel store with an AI shopping assistant (HW4)

A customer website for **Campus Customs** (Yale Bulldog Blue) with a chatbot, **Handsome Dan**:

- **Frontend:** React + Vite + TypeScript. Home, Products, product pages, About, Log in / Create account, and a floating chat.
- **Backend:** FastAPI. Products, photos, auth, and chat endpoints (plain and streaming).
- **Brain:** a Pydantic AI agent that answers price and stock questions from the local SQLite database. It puts matching products on the page as cards, remembers logged-in shoppers, and fact-checks every price and stock number before replying.

Full design notes are in [`output/harness.md`](output/harness.md); start with its *System overview*.

---

## 1. Place the data pack (not in git)

The database and product photos are **not** in this repository. Put the course data pack in a `data/` folder **inside `hw4/`**:

```
hw4/
└── data/
    ├── campus_customs.db
    └── products/          # images referenced by the catalogue (102 .jpg files)
```

On first start the backend adds what it needs to the database (a `sessions` table, a `page_path` column on `chat_messages`, and an index). The original photos are never modified: trimmed copies are cached in `backend/.image_cache/`.

## 2. Configure the API key

```bash
cp .env.example .env        # Windows: copy .env.example .env
```

Edit `.env` and set `PORTKEY_API_KEY` (the course's Portkey key). The model defaults to `gpt-5.6-luna` through the Portkey OpenAI-compatible gateway. `.env` is git-ignored. Without a key the shop, accounts and products still work; only the chat returns "assistant not configured".

## 3. Run the backend (FastAPI + agent): port 8000

Requires Python 3.11+ (developed on 3.13).

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate        macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt

cd backend
uvicorn main:app --reload --port 8000
```

API docs: http://localhost:8000/docs. On the first start, product photos are processed in the background (about 1–2 minutes once, then cached).

## 4. Run the frontend (Vite React TypeScript): port 5173

Requires Node 20+ (developed on Node 24). In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**. Vite proxies `/api` and `/media` to the backend on port 8000, so both must be running.

## 5. Try it

- **Browse:** Products, filter by category, open any item to see its stock per size.
- **Chat:** click Handsome Dan (bottom right) and try:
  - *"What hoodies do you have?"*: the page fills with product cards.
  - *"Gift for my dad, hoodies or t-shirts size L"*: cards show stock for size L.
  - On a product page: *"Do you have this in pink?"*
- **Accounts:** create one, or use the seed test user `test@campuscustoms.yale.edu` / `password`. Logged-in chats are saved and come back when you return.
- **Fact-checker test** (no API key or network needed):
  ```bash
  cd backend
  python test_fact_check.py
  ```

## Repository layout

```
hw4/
├── AI_prompts.md            # log of the prompts used to build this, per problem
├── requirements.txt         # Python dependencies (backend)
├── .env.example             # placeholder config; copy to .env
├── .gitignore               # keeps .env, data/, the DB, images, venv, node_modules out of git
├── README.md
├── frontend/                # Vite React TypeScript app (src/pages, src/components, api.ts …)
├── backend/
│   ├── main.py              # FastAPI app: run with  uvicorn main:app --reload --port 8000
│   ├── agent.py             # ┐
│   ├── models.py            # │ the agent: four files
│   ├── tools.py             # │
│   ├── prompts/prompt.md    # ┘
│   ├── auth.py              # support: password hashing, sessions, login throttling
│   ├── images.py            # support: trims black bars off product photos when serving
│   ├── audit.py             # support: append-only audit trail writer
│   └── test_fact_check.py   # offline test of the price/stock fact-checker
└── output/
    ├── harness.md           # how the system works (models, tools, safety, specs)
    ├── design.md            # Problem 10: styling decisions
    ├── usability.md         # Problem 9: usability improvements
    ├── app_check.html       # Problem 11: hands-on test report (open in a browser)
    ├── app_check_images/    # screenshots linked from app_check.html
    └── audit_trail.json     # append-only log of every agent run
```

The **agent** is the four files `prompts/prompt.md`, `agent.py`, `tools.py` and `models.py`. `main.py` is the web app that runs it, and `auth.py`, `images.py` and `audit.py` are small web-app helpers, not part of the agent.

Campus photos in `frontend/public/images/` are from Wikimedia Commons under free licenses (CC0 / CC BY / CC BY-SA) and are credited in the site footer.
