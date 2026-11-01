# Christmas 2026

Family wish lists and one combined gift list.

**Live site:** https://snthor-phd.github.io/christmas-2026/

| Page | What it is |
|---|---|
| `index.html` | Landing page: one card per person |
| `gift-list.html` / `gift-list.pdf` | Compact shopping list: gift, price, store links, priority, slide # |
| `decks/<person>/` | Each person's deck, viewable in any browser (arrow keys, swipe, `N` for notes) |

## Surprise rule

Every list names a coordinator ("Before buying, check with …"). Tell the coordinator what you're buying, never the recipient. Nothing about who bought what goes on this site.

## How it's built

- `data/gifts.json` is the single source of truth for the gift list.
- `decks/<id>/deck.json` + `decks/<id>/slides/*.html` + `decks/<id>/img/` hold a claude.ai slide deck.
- `tools/build.py` regenerates `index.html`, `gift-list.html`, `gift-list.pdf` and each `decks/<id>/index.html`.

```bash
uv run --with playwright tools/build.py      # HTML + PDF (first run: uv run --with playwright playwright install chromium)
python3 tools/build.py --no-pdf               # HTML only
```

## Adding a person (lists 3–7)

1. Replace one `"placeholder": true` entry in `data/gifts.json` with the person's `name`, `deck`, `theme`, `coordinator`, `prices_as_of` and `gifts`.
2. Put the deck in `decks/<id>/`:
   - **claude.ai slides:** `deck.json`, `slides/`, `img/` (same layout as `decks/thor/`).
   - **PowerPoint / PDF:** export each slide to `slides/NN.png` and keep the original file alongside for download.
   - **Keynote:** export to PDF or PowerPoint on a Mac first.
3. Run the build and push.

Fonts (Fredoka, Nunito Sans) are self-hosted under the SIL Open Font License; see `assets/fonts/`.
