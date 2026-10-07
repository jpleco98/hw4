"""Pydantic / Pydantic AI structured types for the Campus Customs API and shop agent."""

from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, Field


# ---------- catalogue ----------

class SizeStock(BaseModel):
    """Units on hand for one size of one product."""

    size: str
    quantity: int


class ProductSummary(BaseModel):
    """A product card: used on the Products grid and under chat replies."""

    product_id: str
    name: str
    garment_type: str
    category: str = Field(description="Normalized garment group used for filtering")
    short_description: str
    colors: list[str]
    price: float
    image_url: str
    total_stock: int
    sizes: list[SizeStock] = Field(default_factory=list, description="Units per size, XS to XXL (for size badges)")


class ProductDetail(ProductSummary):
    """Everything the single-item page shows."""

    description: str
    search_tags: list[str]
    inventory: list[SizeStock]


# ---------- auth ----------

class SignupRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    email: str = Field(max_length=254)
    password: str = Field(max_length=128)  # capped so huge inputs can't make hashing slow
    confirm_password: str = Field(max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=128)


class UserPublic(BaseModel):
    """The only user shape the API ever returns: never includes password_hash."""

    id: int
    first_name: str
    last_name: str
    name: str
    email: str


# ---------- chat (website <-> FastAPI) ----------

class ChatTurn(BaseModel):
    """One earlier message, sent back by the widget so the agent has conversation context."""

    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


class PageInfo(BaseModel):
    """What the browser says the shopper is looking at. Untrusted: the backend re-checks it against the DB."""

    path: str = Field(default="/", max_length=200, description="Current route, e.g. /products/basic-hoodie-big-yale")
    product_id: str | None = Field(default=None, max_length=120, description="Product detail page that is open")
    results_product_ids: list[str] = Field(
        default_factory=list, max_length=30, description="Chat-result cards currently shown on the page"
    )
    results_title: str | None = Field(default=None, max_length=80, description="Heading of those chat results")


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    history: list[ChatTurn] = Field(default_factory=list, max_length=20)  # used for guests only
    page: PageInfo = Field(default_factory=PageInfo)


class PageResults(BaseModel):
    """Search results the website renders as full product cards on the page (Problem 7)."""

    title: str = Field(description='Heading shown above the grid, e.g. "Hoodies" or "Navy crewnecks under $60".')
    products: list[ProductSummary]


class Verification(BaseModel):
    """Fact-check summary sent to the widget with each reply."""

    prices_checked: int
    quantities_checked: int
    corrected: bool  # True if the agent had to fix a number before answering


class ChatReply(BaseModel):
    """What the chat widget receives. Every product field is built from the DB, never from model text.

    - products: up to 6 highlights shown as mini-cards inside the chat bubble.
    - page: when the shopper browsed a type of item, the full match list for the website to show as cards.
    """

    reply: str
    products: list[ProductSummary] = []
    page: PageResults | None = None
    verification: Verification | None = None
    size: str | None = None  # size the shopper asked about: cards show stock for this size (Problem 11 fix)


class ChatHistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    products: list[ProductSummary] = []
    created_at: str


class ChatHistory(BaseModel):
    """A logged-in shopper's saved conversation (from chat_messages)."""

    messages: list[ChatHistoryItem]


# ---------- agent (Pydantic AI) ----------

MAX_PAGE_RESULTS = 30  # largest result set the page shows (the biggest category, crewnecks, has 29)


class CustomerContext(BaseModel):
    """Who is chatting, loaded from `users` by the session cookie. Never contains the password hash."""

    user_id: int  # used by tools to scope queries to this shopper; not meant to be shown
    first_name: str
    last_name: str
    full_name: str
    email: str
    member_since: str  # users.created_at (UTC)
    returning: bool  # True if they already had saved chat messages before this one


class ViewedProduct(BaseModel):
    """Catalogue facts about the product page that is open, loaded from the DB (not from the browser)."""

    product_id: str
    name: str
    category: str
    garment_type: str
    colors: list[str]
    price: float


class PageItem(BaseModel):
    product_id: str
    name: str
    price: float


PageType = Literal["home", "products", "chat_results", "product", "about", "login", "signup", "other"]


class PageContext(BaseModel):
    """Where the shopper is on the site right now, so "this"/"these" can be resolved."""

    path: str
    page_type: PageType
    product: ViewedProduct | None = None  # set on product detail pages
    results_title: str | None = None  # set on the chat-results view
    results: list[PageItem] = []  # the chat-result cards on screen (for "which of these…?")


class FactCheckReport(BaseModel):
    """What the output validator verified for one reply (shown to the shopper as a small badge)."""

    prices_checked: int = 0
    quantities_checked: int = 0
    retries: int = 0  # how many times the agent had to correct an unsupported number
    last_problems: list[str] = []


@dataclass
class ShopDeps:
    """Per-request context handed to the agent and its tools via RunContext.

    Built by main.py for every chat message: `customer` from the session cookie (None for guests),
    `page` from the browser's PageInfo after validating it against the database.
    """

    customer: CustomerContext | None = None
    page: PageContext | None = None
    fact_check: FactCheckReport = field(default_factory=FactCheckReport)  # filled in by the output validator


class PageResultsSpec(BaseModel):
    """The agent's instruction to update the website with a set of matching products."""

    title: str = Field(
        max_length=80,
        description='Short heading for the results, e.g. "Hoodies", "Navy hoodies in M", "Saybrook College gear".',
    )
    product_ids: list[str] = Field(
        min_length=1,
        max_length=MAX_PAGE_RESULTS,
        description="ALL matching product_id values from search_products `matches`, in the order returned.",
    )


class ShopReply(BaseModel):
    """The agent's structured output.

    The agent only chooses *which* products to show; the backend then loads those
    products from the database, so prices and stock on the cards can't be hallucinated.
    """

    reply: str = Field(description="Friendly answer to the shopper, in light Markdown (bold, short bullet lists).")
    product_ids: list[str] = Field(
        default_factory=list,
        max_length=6,
        description="product_id values (from tool results) of the items to show as cards, best match first. "
        "Empty if no products are relevant.",
    )
    size: str | None = Field(
        default=None,
        description="The size the shopper is shopping for (XS, S, M, L, XL or XXL), if they mentioned one. "
        "The website then shows stock for THAT size on every product card instead of the all-sizes total.",
    )
    page: PageResultsSpec | None = Field(
        default=None,
        description="Set ONLY when the shopper is browsing a type/group of items (e.g. 'what hoodies do you have?'): "
        "the website then shows every match as product cards. Leave null for questions about one specific "
        "product, price/stock checks, or small talk.",
    )


# ---------- agent tool results ----------
# Every value below is read from campus_customs.db at call time; the agent quotes them, never invents them.

StockStatus = Literal["in_stock", "low_stock", "out_of_stock"]
RequestedSizeStatus = Literal["in_stock", "low_stock", "out_of_stock", "size_not_offered"]


class ProductHit(BaseModel):
    """Compact search result returned to the agent by search_products."""

    product_id: str
    name: str
    category: str
    colors: list[str]
    price: float
    total_stock: int
    sizes_in_stock: list[str]


class SearchResults(BaseModel):
    """search_products result. Keeps size-filtered-out matches visible so the agent never says
    "we don't have it" when the truth is "we have it, but not in your size"."""

    matches: list[ProductHit] = Field(description="Best matches first (all have size_filter in stock, if one was given).")
    total_matches: int = Field(description="How many products matched in total (matches is capped at 30).")
    size_filter: str | None = Field(description="Normalized size that matches were required to have in stock.")
    out_of_stock_in_size: list[ProductHit] = Field(
        default_factory=list,
        description="Products matching the query that exist but are OUT OF STOCK in size_filter.",
    )


class ProductInfo(BaseModel):
    """get_product_info: what the product is and what it costs (no stock: that's check_stock's job)."""

    product_id: str
    name: str
    category: str
    garment_type: str
    description: str = Field(description="Full catalogue description; quote or paraphrase it, don't embellish.")
    colors: list[str]
    price: float = Field(description="Price in USD, the same for every size.")
    currency: Literal["USD"] = "USD"
    sizes_offered: list[str]


class SizeAvailability(BaseModel):
    size: str
    quantity: int = Field(description="Exact units on hand right now.")
    status: StockStatus


class StockReport(BaseModel):
    """check_stock: live inventory for one product, optionally focused on one size."""

    product_id: str
    name: str
    price: float
    requested_size: str | None = Field(description="The size asked about, normalized (e.g. 'medium' -> 'M'), or None.")
    requested_size_status: RequestedSizeStatus | None = Field(
        description="Status of requested_size; None when no size was asked about."
    )
    requested_size_quantity: int | None = Field(description="Units of requested_size (0 if out or not offered).")
    sizes: list[SizeAvailability] = Field(description="Every size offered, XS to XXL.")
    in_stock_sizes: list[str]
    out_of_stock_sizes: list[str]
    total_units: int
    low_stock_threshold: int = Field(description="A size with this many units or fewer counts as low_stock.")
    checked_at: str = Field(description="UTC timestamp of the lookup; stock can change, so re-check rather than reuse.")


class LookupMiss(BaseModel):
    """Returned instead of ProductInfo/StockReport when the product_id doesn't exist."""

    requested: str
    message: str
    suggestions: list[ProductHit] = Field(description="Closest catalogue matches to offer instead (may be empty).")


class CustomerProfile(BaseModel):
    """get_my_account: the logged-in shopper's own account summary."""

    full_name: str
    first_name: str
    email: str
    member_since: str
    saved_messages: int
    first_chat_at: str | None


class PastMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    created_at: str
    products: list[str] = Field(default_factory=list, description='Products shown with this message, as "Name (product_id)"')


class MemorySearch(BaseModel):
    """search_my_chat_history: matching messages from this shopper's saved conversations."""

    query: str
    matches: list[PastMessage]
    total_saved_messages: int


class GuestOnly(BaseModel):
    """Returned by account tools when the shopper isn't logged in."""

    message: str = "The shopper is a guest (not logged in), so there is no account or saved history."


# ---------- audit trail (Problem 12) ----------

AuditStopReason = Literal[
    "final_answer",  # agent produced a validated ShopReply
    "content_filter",  # provider blocked the message; shopper got a polite refusal
    "fact_check_exhausted",  # every draft failed the price/stock fact-check; safe fallback reply shown
    "usage_limit",  # hit request/tool-call loop limits
    "model_error",  # provider/network/other failure
    "not_configured",  # no API key
]


class AuditStep(BaseModel):
    """One event in the agent loop, in order."""

    step: int
    time: str  # UTC ISO timestamp of the message the event came from
    kind: Literal["model_request", "tool_call", "tool_result", "retry", "final_output"]
    tool: str | None = None  # tool name (final_result = the structured answer)
    args: str | None = None  # tool arguments, JSON, truncated
    result: str | None = None  # tool result / retry feedback / model finish reason, truncated


class AuditEntry(BaseModel):
    """One chat message = one agent run. Appended to output/audit_trail.json, never rewritten."""

    run_id: str
    started_at: str
    duration_ms: int
    endpoint: Literal["/api/chat", "/api/chat/stream"]
    model: str
    shopper: str  # "guest" or "user:<id>"; never email/name, so the log holds no personal data
    page: str | None  # page path the shopper was on
    message: str  # shopper's message, truncated
    history_turns: int  # earlier turns given to the agent as context
    steps: list[AuditStep]
    model_requests: int
    tool_calls: int
    input_tokens: int | None = None
    output_tokens: int | None = None
    stop_reason: AuditStopReason
    error: str | None = None  # exception type + short message when the run failed
    fact_check: FactCheckReport | None = None
    reply: str | None = None  # final reply text, truncated
    product_ids: list[str] = []
    page_results: int | None = None  # number of cards put on the page, if any
    size: str | None = None
