"""Tools the Campus Customs agent can call, plus the database helpers they share with main.py.

Every fact the chatbot states about price, colors or stock comes from these functions,
which read data/campus_customs.db directly. The two account tools (get_my_account,
search_my_chat_history) only ever read the *logged-in shopper's own* rows: the user id
comes from ShopDeps (set by the server from the session cookie), never from the model.
No tool can read passwords, sessions or other shoppers' data.
"""

import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from pydantic_ai import RunContext

from models import (
    CustomerProfile,
    GuestOnly,
    MemorySearch,
    PageContext,
    PageInfo,
    PageItem,
    PastMessage,
    ShopDeps,
    ViewedProduct,
    MAX_PAGE_RESULTS,
    LookupMiss,
    ProductDetail,
    ProductHit,
    ProductInfo,
    ProductSummary,
    SearchResults,
    SizeAvailability,
    SizeStock,
    StockReport,
)

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE.parent / "data"
DB_PATH = DATA_DIR / "campus_customs.db"

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]

# The DB has 22 inconsistent garment_type labels; collapse them into shop categories.
# Order matters: "full-zip hooded sweatshirt" is a hoodie, not a crewneck.
CATEGORY_RULES = [
    ("Hoodies", ("hood",)),
    ("Quarter-Zips", ("quarter-zip",)),
    ("Jackets & Fleece", ("jacket", "fleece")),
    ("Crewnecks", ("crewneck", "mockneck")),
    ("Long Sleeve", ("long-sleeve",)),
    ("T-Shirts", ("t-shirt",)),
]

MAX_SEARCH_RESULTS = MAX_PAGE_RESULTS  # enough to fill the page with a whole category


# ---------- database helpers (shared with main.py) ----------

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def categorize(garment_type: str) -> str:
    g = garment_type.lower()
    for category, keys in CATEGORY_RULES:
        if any(k in g for k in keys):
            return category
    return "Other"


def list_categories() -> list[str]:
    with get_conn() as conn:
        found = {categorize(r[0]) for r in conn.execute("SELECT DISTINCT garment_type FROM catalogue")}
    return [c for c, _ in CATEGORY_RULES if c in found] + (["Other"] if "Other" in found else [])


def short(text: str, limit: int = 110) -> str:
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0].rstrip(",.;") + "…"


PRODUCT_SELECT = """
    SELECT c.*, COALESCE(SUM(i.quantity), 0) AS total_stock,
           GROUP_CONCAT(i.size || ':' || i.quantity) AS stock_csv
    FROM catalogue c LEFT JOIN inventory i ON i.product_id = c.product_id
"""


def _sizes_from_csv(csv: str | None) -> list[SizeStock]:
    pairs = [part.split(":") for part in (csv or "").split(",") if ":" in part]
    sizes = [SizeStock(size=size, quantity=int(qty)) for size, qty in pairs]
    return sorted(sizes, key=lambda s: SIZE_ORDER.index(s.size) if s.size in SIZE_ORDER else 99)


def to_summary(row: sqlite3.Row) -> ProductSummary:
    return ProductSummary(
        product_id=row["product_id"],
        name=row["name"],
        garment_type=row["garment_type"],
        category=categorize(row["garment_type"]),
        short_description=short(row["description"]),
        colors=json.loads(row["colors"]),
        price=row["price"],
        image_url=f"/media/{row['image_file_path']}",
        total_stock=row["total_stock"] or 0,
        sizes=_sizes_from_csv(row["stock_csv"]) if "stock_csv" in row.keys() else [],
    )


def list_products(q: str | None = None, category: str | None = None) -> list[ProductSummary]:
    sql, params = PRODUCT_SELECT, []
    if q:
        like = f"%{q.lower()}%"
        sql += " WHERE lower(c.name) LIKE ? OR lower(c.description) LIKE ? OR lower(c.search_tags) LIKE ?"
        params = [like, like, like]
    sql += " GROUP BY c.product_id ORDER BY c.name"
    with get_conn() as conn:
        products = [to_summary(r) for r in conn.execute(sql, params)]
    if category:
        products = [p for p in products if p.category == category]
    return products


def load_product_detail(product_id: str) -> ProductDetail | None:
    with get_conn() as conn:
        row = conn.execute(PRODUCT_SELECT + " WHERE c.product_id = ? GROUP BY c.product_id", (product_id,)).fetchone()
        if row is None:
            return None
        stock = conn.execute("SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,)).fetchall()
    inventory = sorted(
        (SizeStock(size=s["size"], quantity=s["quantity"]) for s in stock),
        key=lambda s: SIZE_ORDER.index(s.size) if s.size in SIZE_ORDER else len(SIZE_ORDER),
    )
    return ProductDetail(
        **to_summary(row).model_dump(),
        description=row["description"],
        search_tags=json.loads(row["search_tags"]),
        inventory=inventory,
    )


def summaries_by_ids(product_ids: list[str]) -> list[ProductSummary]:
    """Product cards for the given IDs, in the given order; unknown IDs are silently dropped."""
    ids = list(dict.fromkeys(product_ids))  # de-duplicate, keep order
    if not ids:
        return []
    marks = ",".join("?" * len(ids))
    with get_conn() as conn:
        rows = conn.execute(PRODUCT_SELECT + f" WHERE c.product_id IN ({marks}) GROUP BY c.product_id", ids)
        found = {r["product_id"]: to_summary(r) for r in rows}
    return [found[i] for i in ids if i in found]


# ---------- agent tools ----------

STOPWORDS = {
    "a", "an", "and", "any", "do", "for", "have", "i", "in", "is", "me", "my", "of", "on", "or",
    "show", "some", "the", "to", "with", "you", "your", "yale", "want", "looking", "something",
}


def _terms(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    # crude singularization so "hoodies" matches "hoodie"
    return [w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w for w in words if w not in STOPWORDS]


def search_products(
    query: str = "",
    category: str | None = None,
    color: str | None = None,
    max_price: float | None = None,
    size: str | None = None,
) -> SearchResults:
    """Search the Campus Customs catalogue. Use this before recommending or naming any product.

    Args:
        query: Free-text keywords, e.g. "saybrook crewneck", "hockey", "dad hoodie". May be empty when filtering only.
        category: Optional exact category: Hoodies, Crewnecks, T-Shirts, Quarter-Zips, Jackets & Fleece, Long Sleeve.
        color: Optional color word to require, e.g. "navy", "gray", "white".
        max_price: Optional maximum price in USD.
        size: Optional size that must be in stock (XS, S, M, L, XL, XXL; "medium" etc. also work).

    Returns up to 30 `matches`, best first, each with price, colors, total stock and the sizes in stock.
    With a size filter, `out_of_stock_in_size` lists products that match the query but are sold out in that size.
    No matches and no out_of_stock_in_size means nothing in the catalogue matches.
    """
    terms = _terms(query)
    size = normalize_size(size)
    with get_conn() as conn:
        rows = conn.execute(PRODUCT_SELECT + " GROUP BY c.product_id").fetchall()
        stock: dict[str, list[str]] = {}
        for r in conn.execute("SELECT product_id, size FROM inventory WHERE quantity > 0"):
            stock.setdefault(r["product_id"], []).append(r["size"])

    # (all_terms_matched, score, hit)
    scored: list[tuple[bool, int, ProductHit]] = []
    no_size: list[tuple[bool, int, ProductHit]] = []
    for r in rows:
        colors = json.loads(r["colors"])
        cat = categorize(r["garment_type"])
        if category and cat.lower() != category.lower():
            continue
        if color and not any(color.lower() in c.lower() for c in colors):
            continue
        if max_price is not None and r["price"] > max_price:
            continue
        sizes = sorted(stock.get(r["product_id"], []), key=lambda s: SIZE_ORDER.index(s) if s in SIZE_ORDER else 99)
        name = r["name"].lower()
        haystack = " ".join([name, r["garment_type"], r["description"], r["search_tags"], " ".join(colors), cat]).lower()
        hits = sum(1 for t in terms if t in haystack)
        if terms and hits == 0:
            continue
        score = hits * 10 + sum(5 for t in terms if t in name)
        (scored if not size or size in sizes else no_size).append(
            (
                hits == len(terms),
                score,
                ProductHit(
                    product_id=r["product_id"],
                    name=r["name"],
                    category=cat,
                    colors=colors,
                    price=r["price"],
                    total_stock=r["total_stock"] or 0,
                    sizes_in_stock=sizes,
                ),
            )
        )
    # Prefer products matching every keyword ("saybrook college" -> Saybrook items only, not every
    # product tagged "college"); fall back to partial matches when nothing matches them all.
    if any(full for full, _, _ in scored):
        scored = [s for s in scored if s[0]]
    if any(full for full, _, _ in no_size):
        no_size = [s for s in no_size if s[0]]
    scored.sort(key=lambda s: (-s[1], s[2].name))
    no_size.sort(key=lambda s: (-s[1], s[2].name))
    return SearchResults(
        matches=[hit for _, _, hit in scored[:MAX_SEARCH_RESULTS]],
        total_matches=len(scored),
        size_filter=size,
        # only worth reporting when the shopper searched for something specific
        out_of_stock_in_size=[hit for _, _, hit in no_size[:3]] if terms else [],
    )


LOW_STOCK_THRESHOLD = 3  # same "Only N left" rule the product page uses

SIZE_ALIASES = {
    "XS": "XS", "XSMALL": "XS", "EXTRASMALL": "XS", "XSM": "XS",
    "S": "S", "SM": "S", "SMALL": "S",
    "M": "M", "MD": "M", "MED": "M", "MEDIUM": "M",
    "L": "L", "LG": "L", "LARGE": "L",
    "XL": "XL", "XLARGE": "XL", "EXTRALARGE": "XL", "1XL": "XL",
    "XXL": "XXL", "2XL": "XXL", "XXLARGE": "XXL", "2XLARGE": "XXL", "EXTRAEXTRALARGE": "XXL",
}


def normalize_size(size: str | None) -> str | None:
    """'medium' -> 'M', 'x-large' -> 'XL', '2XL' -> 'XXL'. Unknown sizes come back upper-cased, unchanged."""
    if not size or not size.strip():
        return None
    key = re.sub(r"[^A-Z0-9]", "", size.upper())
    return SIZE_ALIASES.get(key, size.strip().upper())


def _stock_status(qty: int) -> str:
    if qty <= 0:
        return "out_of_stock"
    return "low_stock" if qty <= LOW_STOCK_THRESHOLD else "in_stock"


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _find_product_row(conn: sqlite3.Connection, ref: str) -> sqlite3.Row | None:
    """Match by product_id first, then by exact name (agents sometimes pass the name instead of the id)."""
    ref = ref.strip()
    for value in (ref, _slug(ref)):
        row = conn.execute("SELECT * FROM catalogue WHERE product_id = ?", (value,)).fetchone()
        if row:
            return row
    return conn.execute("SELECT * FROM catalogue WHERE lower(name) = ?", (ref.lower(),)).fetchone()


def _miss(ref: str) -> LookupMiss:
    return LookupMiss(
        requested=ref,
        message=f"No Campus Customs product matches '{ref}'. Don't guess; offer the suggestions or search again.",
        suggestions=search_products(ref).matches[:3],
    )


def get_product_info(product_id: str) -> ProductInfo | LookupMiss:
    """Look up what a product is and what it costs: full description, colors, price (USD) and sizes offered.

    Call this for questions about a product's price, look, colors or description.
    For "is it in stock / how many / do you have my size" use check_stock instead.

    Args:
        product_id: The product_id from a search_products result (an exact product name also works).
    """
    with get_conn() as conn:
        row = _find_product_row(conn, product_id)
        if row is None:
            return _miss(product_id)
        sizes = [r[0] for r in conn.execute("SELECT size FROM inventory WHERE product_id = ?", (row["product_id"],))]
    return ProductInfo(
        product_id=row["product_id"],
        name=row["name"],
        category=categorize(row["garment_type"]),
        garment_type=row["garment_type"],
        description=row["description"],
        colors=json.loads(row["colors"]),
        price=row["price"],
        sizes_offered=sorted(sizes, key=lambda s: SIZE_ORDER.index(s) if s in SIZE_ORDER else 99),
    )


def check_stock(product_id: str, size: str | None = None) -> StockReport | LookupMiss:
    """Live inventory for one product: exact units per size, with in_stock / low_stock / out_of_stock status.

    Call this for EVERY availability question ("in stock?", "how many?", "do you have it in M?"),
    even if stock was mentioned earlier in the chat, because inventory changes.

    Args:
        product_id: The product_id from a search_products result (an exact product name also works).
        size: Optional size the shopper asked about, e.g. "M", "medium", "XL", "2XL".
    """
    wanted = normalize_size(size)
    with get_conn() as conn:
        row = _find_product_row(conn, product_id)
        if row is None:
            return _miss(product_id)
        rows = conn.execute("SELECT size, quantity FROM inventory WHERE product_id = ?", (row["product_id"],)).fetchall()
    sizes = sorted(
        (SizeAvailability(size=r["size"], quantity=r["quantity"], status=_stock_status(r["quantity"])) for r in rows),
        key=lambda s: SIZE_ORDER.index(s.size) if s.size in SIZE_ORDER else 99,
    )
    by_size = {s.size: s for s in sizes}
    if wanted is None:
        req_status, req_qty = None, None
    elif wanted in by_size:
        req_status, req_qty = by_size[wanted].status, by_size[wanted].quantity
    else:
        req_status, req_qty = "size_not_offered", 0
    return StockReport(
        product_id=row["product_id"],
        name=row["name"],
        price=row["price"],
        requested_size=wanted,
        requested_size_status=req_status,
        requested_size_quantity=req_qty,
        sizes=sizes,
        in_stock_sizes=[s.size for s in sizes if s.quantity > 0],
        out_of_stock_sizes=[s.size for s in sizes if s.quantity <= 0],
        total_units=sum(s.quantity for s in sizes),
        low_stock_threshold=LOW_STOCK_THRESHOLD,
        checked_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
    )


# ---------- customer memory tools ----------

def get_my_account(ctx: RunContext[ShopDeps]) -> CustomerProfile | GuestOnly:
    """The logged-in shopper's own account: name, email, member-since date and how much chat history is saved.

    Use when the shopper asks about their account ("what email am I using?", "since when am I a member?").
    """
    c = ctx.deps.customer
    if c is None:
        return GuestOnly()
    with get_conn() as conn:
        count, first = conn.execute(
            "SELECT COUNT(*), MIN(created_at) FROM chat_messages WHERE user_id = ?", (c.user_id,)
        ).fetchone()
    return CustomerProfile(
        full_name=c.full_name,
        first_name=c.first_name,
        email=c.email,
        member_since=c.member_since,
        saved_messages=count,
        first_chat_at=first,
    )


def search_my_chat_history(ctx: RunContext[ShopDeps], query: str = "", limit: int = 6) -> MemorySearch | GuestOnly:
    """Search the logged-in shopper's OWN saved past conversations (older than what you already see).

    Use for "what was that hoodie you showed me last time?", "what did I ask about before?".

    Args:
        query: Keywords to look for, e.g. "hoodie", "saybrook", "XL". Empty returns the most recent messages.
        limit: Max messages to return (1-10).
    """
    c = ctx.deps.customer
    if c is None:
        return GuestOnly()
    limit = max(1, min(limit, 10))
    terms = _terms(query)
    sql = "SELECT role, content, products_json, created_at FROM chat_messages WHERE user_id = ?"
    params: list = [c.user_id]
    if terms:
        sql += " AND (" + " OR ".join("lower(content) LIKE ? OR lower(COALESCE(products_json, '')) LIKE ?" for _ in terms) + ")"
        for t in terms:
            params += [f"%{t}%", f"%{t}%"]
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
        total = conn.execute("SELECT COUNT(*) FROM chat_messages WHERE user_id = ?", (c.user_id,)).fetchone()[0]
    matches = []
    for r in rows:
        names: list[str] = []
        try:
            names = [
                f"{p.get('name', '')} ({p.get('product_id', '')})"
                for p in json.loads(r["products_json"] or "[]")
                if isinstance(p, dict)
            ]
        except json.JSONDecodeError:
            pass
        content = r["content"] if len(r["content"]) <= 400 else r["content"][:400] + "…"
        matches.append(PastMessage(role=r["role"], content=content, created_at=r["created_at"], products=names))
    return MemorySearch(query=query, matches=matches, total_saved_messages=total)


AGENT_TOOLS = [search_products, get_product_info, check_stock, get_my_account, search_my_chat_history]


# ---------- page context (built by main.py, read by the agent through ShopDeps) ----------

STATIC_PAGES = {"/": "home", "/about": "about", "/login": "login", "/signup": "signup"}


def build_page_context(info: PageInfo) -> PageContext:
    """Turn the browser's PageInfo into trusted context: every product fact is re-read from the DB.

    Free-text fields from the browser end up in the agent's instructions, so they are reduced to
    safe characters first (otherwise a crafted "path" could smuggle in prompt-injection text).
    """
    path = re.sub(r"[^A-Za-z0-9/_\-]", "", info.path.split("?")[0])[:120] or "/"
    page_type = STATIC_PAGES.get(path, "other")
    product = None
    if path.startswith("/products/"):
        page_type = "product"
        pid = info.product_id or path.removeprefix("/products/")
        with get_conn() as conn:
            row = conn.execute("SELECT * FROM catalogue WHERE product_id = ?", (pid,)).fetchone()
        if row:
            product = ViewedProduct(
                product_id=row["product_id"],
                name=row["name"],
                category=categorize(row["garment_type"]),
                garment_type=row["garment_type"],
                colors=json.loads(row["colors"]),
                price=row["price"],
            )
    elif path == "/products":
        page_type = "chat_results" if info.results_product_ids else "products"
    results = []
    if page_type == "chat_results":
        results = [PageItem(product_id=p.product_id, name=p.name, price=p.price) for p in summaries_by_ids(info.results_product_ids)]
    return PageContext(
        path=path,
        page_type=page_type,
        product=product,
        results_title=re.sub(r"[^\w $&'.,-]", "", info.results_title or "")[:80] or None if results else None,
        results=results,
    )


# ---------- fact-checking (used by the output validator in agent.py) ----------

PRICE_KEYS = {"price"}
QUANTITY_KEYS = {"quantity", "requested_size_quantity", "total_units", "total_stock", "total_matches",
                 "saved_messages", "low_stock_threshold"}

PRICE_RE = re.compile(r"\$\s?(\d{1,4}(?:\.\d{1,2})?)")
SIZE_WORD = r"(?:xx?s|xx?l|2xl|s|m|l|smalls?|mediums?|larges?|x-larges?|extra[- ]larges?)"
QTY_RE = re.compile(
    rf"\b(\d{{1,4}})\s+(?:{SIZE_WORD}\s+)?(?:units?|left|in stock|available|remaining|pieces?)\b"
    r"|\bonly\s+(\d{1,4})\b",
    re.IGNORECASE,
)


def _walk(value, prices: set[float], quantities: set[int]) -> None:
    if hasattr(value, "model_dump"):
        value = value.model_dump()
    if isinstance(value, dict):
        for k, v in value.items():
            if k in PRICE_KEYS and isinstance(v, (int, float)):
                prices.add(round(float(v), 2))
            elif k in QUANTITY_KEYS and isinstance(v, int):
                quantities.add(v)
            else:
                _walk(v, prices, quantities)
    elif isinstance(value, (list, tuple)):
        for v in value:
            _walk(v, prices, quantities)


def collect_facts(tool_results: list, deps: ShopDeps, user_texts: list[str]) -> tuple[set[float], set[int]]:
    """Every price and quantity the agent is allowed to state in this run:
    values returned by tools, DB facts in the page context, and numbers the shopper typed themselves."""
    prices: set[float] = set()
    quantities: set[int] = set()
    for content in tool_results:
        _walk(content, prices, quantities)
    if deps.page:
        _walk(deps.page, prices, quantities)
    for text in user_texts:
        for m in re.findall(r"\d+(?:\.\d{1,2})?", text):
            prices.add(round(float(m), 2))
            quantities.add(int(float(m)))
    return prices, quantities


def check_reply(reply: str, prices: set[float], quantities: set[int]) -> tuple[list[str], int, int]:
    """Return (problems, n_prices_checked, n_quantities_checked) for the numbers stated in `reply`."""
    text = reply.replace("**", "").replace(",", "")
    problems: list[str] = []
    stated_prices = [round(float(m), 2) for m in PRICE_RE.findall(text)]
    stated_qty = [int(a or b) for a, b in QTY_RE.findall(text)]
    for value in stated_prices:
        if value not in prices:
            problems.append(f"price ${value:.2f} does not match any price returned by the tools")
    for value in stated_qty:
        if value not in quantities:
            problems.append(f"quantity {value} does not match any stock number returned by the tools")
    return problems, len(stated_prices), len(stated_qty)
