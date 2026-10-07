# HW4 — Usability Improvements (Problem 9)

Four improvements to the working shop: two on the frontend (look and ease of use) and two on the agent/backend (faster, more accurate, safer). Each section says what was added, why it helps a Campus Customs shopper or the business, and **where to see it in the running app** (backend: `uvicorn main:app --port 8000` from `backend/`; frontend: `npm run dev` in `frontend/`, open http://localhost:5173).

---

## 1. Frontend — Size picker + stock badges

**What we added.** Every product card now has a **size strip** under the price (XS S M L XL XXL). Sizes in stock are blue, sizes with 3 or fewer left are orange, and sold-out sizes are grey and struck through. Urgent cards also get a corner badge: **"Almost gone: N left"** (20 units or fewer in total) or **"Few sizes left"** (half the sizes or more sold out). On the single-item page, the old stock table was replaced by a **size picker**: tappable XS–XXL buttons that show "In stock", "2 left" or "Sold out", with a live message under them ("Only 2 left in L, order soon" / "Sold out in XXL"). Picking a sold-out size shows a **"💬 Ask the assistant for alternatives"** button that opens the chat and asks for similar items in that size. **Why it helps.** Shoppers see straight away whether their size exists, before reading a description or opening a product, so they don't fall in love with a hoodie that's sold out in M. For the business, the low-stock badges create honest urgency, and the alternatives button turns a dead end (sold out) into a recommendation, which keeps the sale. *Where to see it:* `/products` (size strips and badges, e.g. Saybrook College Crewneck shows L in orange and XXL struck through). Open that product, then tap **L** and **XXL**.

## 2. Frontend — Mobile & accessibility polish

**What we added.**
- **Mobile layout:**
  - Under 860 px the nav collapses behind a **☰ menu button** (with `aria-expanded`), and the menu closes itself after you navigate.
  - On phones (under 600 px) the chat opens as a **full-screen sheet**, with a 16 px input so iOS doesn't zoom.
  - The product grid shows 2 columns, and touch targets are at least 44 px.
- **Keyboard and screen readers:**
  - A **"Skip to content"** link and clear **focus outlines** for keyboard users.
  - The chat panel is a labelled dialog: focus moves to the input when it opens, **Escape closes it**, and focus returns to the chat button.
  - A screen-reader **live region** announces the tool status and the finished reply (not every streamed word).
  - The size picker is a proper `radiogroup`.
- **Loading and motion:** **skeleton placeholders**, shaped like product cards and the product page, replace the "Loading…" text, and animations are switched off for users who prefer reduced motion.

**Why it helps.** Students shop from their phones, between classes or at the game, so the site has to work one-handed on a small screen. The old nav and floating chat box were cramped there. Accessibility makes the store usable for shoppers who rely on keyboards or screen readers (important for a university-licensed shop), and skeletons make the site feel faster and stop the layout jumping while data loads. *Where to see it:* shrink the browser (or use device mode) to phone width. Then try ☰, open the chat (full screen), and press Tab from the top of any page to see the skip link.

## 3. Agent/backend — Price & stock fact-checker

**What we added.** A Pydantic AI **output validator** (`fact_check` in `backend/agent.py`, helpers `collect_facts` / `check_reply` in `backend/tools.py`). Before any reply reaches the shopper, it extracts every **$ price** and every **stock count** ("2 left", "15 in stock") from the text. It then checks each one against the values the tools actually returned in that run, plus the DB-sourced page context and numbers the shopper typed. If any number doesn't match, it raises `ModelRetry` with the exact problem ("price $45.00 does not match any price returned by the tools"). The agent then has to look it up and fix the reply (up to 2 retries). If it still can't, the shopper gets a safe "please check the product page" message instead of an unverified number. Every verified reply shows a small green **"✓ Verified against live inventory"** badge in the chat (hover for what was checked), or "Corrected & verified" when a fix was needed. **Why it helps.** A chatbot that quotes a wrong price or promises stock that isn't there causes angry customers at the register and lost trust, and for a licensed shop that can become a real business problem. This guarantees, in code rather than just in the prompt, that the numbers shoppers read come from the database. The badge tells them they can rely on it. *Where to see it:* ask the chat "How many larges of the Saybrook crewneck are left and how much is it?". The reply ("2 larges left… $58.00") carries the ✓ badge. The correction itself is shown by `backend/test_fact_check.py` (no API key needed): a scripted model first says "$45, 4 left", the validator rejects it, and the final answer is "$58, 2 left".

## 4. Agent/backend — Streaming replies + live tool status

**What we added.** A new endpoint, **`POST /api/chat/stream`**, streams the agent's work as NDJSON events while it happens. `stream_chat()` in `backend/agent.py` reads Pydantic AI's `run_stream_events`:
- When a tool starts, it sends a **live status line** ("Searching navy hoodies in size M…", "Checking live stock for Saybrook College Crewneck (XXL)…", "Double-checking prices & stock…").
- While the model writes its answer, it parses the partial structured output and sends the **reply text as it grows**.
- If the fact-checker rejects a draft, it sends a `reset` so the half-written text is cleared.

The chat widget reads the stream with `fetch` and shows the status next to the typing dots, then the words appearing with a blinking cursor. The final, validated reply (cards, page results, verified badge) replaces it at the end. The old `/api/chat` endpoint still works for scripts. **Why it helps.** A reply takes several seconds because the agent searches and checks stock first. Before, shoppers stared at three dots and often assumed the bot was broken. Now they see progress within about 1–2 seconds and the first words after about 4–5 seconds. That makes the wait feel shorter, explains *why* it takes a moment (it's checking real stock), and keeps people chatting, which the business wants. *Where to see it:* open the chat and ask "Do you have the Saybrook crewneck in XXL?". Watch the status lines change, then the answer type itself out.
