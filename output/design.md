# HW4 — Design (Problem 10: Style the Website)

**Goal:** make the site feel like a real Campus Customs storefront instead of a default template, so shoppers stay longer and buy. Premium apparel sites (Ralph Lauren, Abercrombie) open with a big photograph and a short story *before* the product grid, use a distinctive serif, and keep the palette tight. We followed that pattern and kept Yale Blue at the center.

---

### 1. Hero-first, editorial home page
**What changed.** The home page now opens on a **full-screen photo of Harkness Tower against a blue sky**, with a slow "Ken Burns" zoom, a giant headline (**"Wear the *Blue.*"**) and two clear actions: *Shop the collection* and *Ask Handsome Dan*. The nav floats transparently over the photo and turns solid Yale blue once you scroll. Below that, the page tells a story before selling:
- a scrolling varsity ribbon ("Boola Boola ✦ Officially licensed ✦ 57 Broadway…");
- **The Edit**, three large category tiles (Hoodies, Crewnecks, Game Day) with oversized product shots;
- a **split section** with students on Old Campus ("Made for the walk *to class*");
- the bestsellers;
- a **Meet Handsome Dan** band;
- a **Visit the shop** section over an autumn street photo.

The About page also opens on a photo (the Memorial Quadrangle gate, "Lux et Veritas").

**Why it helps people buy.** The first screen sells the *feeling* (being part of Yale) before asking for anything. That's what makes a $68 hoodie feel worth it, and it's the moment a first-time visitor decides whether to keep scrolling. Category tiles and the split section give quick, confident paths into the catalogue ("I want a hoodie"), instead of facing 102 items at once.

*Photos:* four freely licensed Yale campus photos from Wikimedia Commons, resized for the web, each credited on the photo and in the footer's "Photo credits" (CC0, CC BY, CC BY-SA, as their licenses require).

### 2. Typography with a point of view
**What changed.** We replaced the default system sans and Georgia with three self-hosted fonts, each with one job:
- **Fraunces**, a modern variable serif, for headlines and prices. It's elegant at display sizes, with an italic used for accents.
- **Figtree**, a clean, friendly sans, for body text, buttons and forms.
- **Graduate**, a varsity block face, for small labels ("THE EDIT", category tags, the ribbon).

Buttons became square, uppercase and letter-spaced. Hierarchy is now clear: a big serif headline, then a small varsity label, then readable body text. **Why it helps.** The serif signals heritage and quality (a licensed university shop, not a dropshipper). The varsity labels make it unmistakably *collegiate*, and one consistent hierarchy makes pages faster to scan, so shoppers find what they want sooner.

### 3. A refined Yale Blue palette
**What changed.** Yale Blue (`#00356B`) stays the hero color, but it now has a supporting cast:
- a deep **midnight** navy for the footer, ribbons and overlays;
- a soft **sky blue** for accents (the italic "*Blue.*");
- warm **ivory paper** (`#F8F5EF`) instead of cold grey for backgrounds, with **stone** borders;
- muted, purposeful status colors for low stock and sold out.

**Why it helps.** Ivory and navy read as classic collegiate retail. The old bright-blue-on-grey read as an app dashboard. A tight palette makes the important things stand out (Yale-blue buttons, orange "Almost gone" badges) and builds trust that this is the official store.

### 4. Handsome Dan, the chat persona
**What changed.** The generic chat bubble is now **Handsome Dan**, named after Yale's bulldog mascot:
- **The launcher:** a hand-drawn SVG bulldog (Yale-blue collar, "Y" tag) with a green "online" dot. A one-time speech tip pops up after a few seconds: *"Need a size? Ask me, I check live stock."*
- **The chat panel:** a branded header ("Handsome Dan · Online"), Dan's avatar beside each reply, page-aware **starter questions** in a fresh chat, and swipeable product cards.
- **The agent:** its system prompt now speaks as Dan. It allows at most one playful touch per reply ("Woof!"), and facts always come first.
- **Elsewhere:** Dan also has a section on the home page, with one-tap example questions, and an "Ask Dan" box on every product page.

**Why it helps.** A named mascot shoppers already love turns the assistant from "a widget" into part of the store, so more people try it. Every chat is a guided path to the right size or an in-stock alternative, which is where the sale is won or lost. The proactive tip and the product-page box put help exactly where a shopper hesitates.

### 5. Motion & product presentation (supporting)
- **Motion:** sections **fade up as you scroll**, product photos zoom gently on hover with a "View details →" bar, nav links get a sliding underline, and Dan's chat panel springs open. All of it is switched off for users who prefer reduced motion.
- **Product photos:** they fill their tiles edge to edge. After the Problem 11 app check, the backend also **trims the black bars** baked into 73 of the 102 catalogue photos and whitens fully black backgrounds (41 of 45; the 4 near-black navy garments are deliberately left on black so they aren't damaged). Result: a uniform, premium grid. See `app_check.html`, check 4.

**Why it helps.** Subtle motion makes the site feel alive and premium and draws the eye to the next thing to click, without slowing anyone down.

---

**Where to see it:** run the site and open `/` (hero, ribbon, The Edit, Old Campus split, Meet Dan, Visit), `/about` (gate hero), `/products` and any product page (cards, "Ask Dan" box), and the Dan launcher in the bottom-right corner on every page.
