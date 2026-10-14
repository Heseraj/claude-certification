# Frontend Changes

## Theme toggle button (dark / light)

A round, icon-based button fixed to the top-right corner switches the UI between the existing dark theme and a new light theme.

### `frontend/index.html`
- Added `<button id="themeToggle" class="theme-toggle">` at the top of `<body>`. It holds two stacked inline SVGs: a **sun** (shown in dark mode, meaning "switch to light") and a **moon** (shown in light mode). Both SVGs are `aria-hidden`; the button carries an `aria-label`/`title`.
- Added a small inline script in `<head>` that applies a saved light theme (`localStorage.theme`) **before first paint**, so the page doesn't flash dark on reload.
- Bumped the cache-busting query strings to `style.css?v=14` / `script.js?v=14`.

### `frontend/style.css`
- **Light palette**: a `[data-theme="light"]` block overrides the existing `:root` CSS variables. Dark stays the default.
- Added three new variables so previously hardcoded colors adapt to the theme: `--code-bg` (inline code / `pre` background), `--error-text`, `--success-text`.
- **`.theme-toggle`**: 40px circular button using `--surface`, `--border-color` and `--shadow`. Its hover lift and blue accent match the send button and suggested items, and it uses the same `--focus-ring` style on `:focus-visible`.
- **Icon animation**: the inactive icon is rotated ±90°, scaled to 0.5 and faded out; toggling animates both icons (0.4s transform, 0.3s opacity).
- **Smooth theme crossfade**: a temporary `.theme-transition` class on `<html>` animates background, text, border and shadow colors over 0.3s. It is applied only during the switch, so the existing hover transitions keep their normal speed.
- `prefers-reduced-motion: reduce` turns off the toggle and icon animations.

### `frontend/script.js`
- `toggleTheme()` flips `data-theme` on `<html>`, adds `.theme-transition` for 300ms, and saves the choice to `localStorage` (wrapped in try/catch so it still works when storage is blocked).
- `updateThemeToggleLabel()` keeps `aria-label`/`title` describing the action ("Switch to light theme" / "Switch to dark theme"). It runs on load and after each toggle.
- `getCurrentTheme()` is a small helper; the click listener is registered in `setupEventListeners()`.

### Accessibility
- It is a native `<button type="button">`, so it can be reached with Tab and activated with Enter or Space without extra key handling.
- Visible focus ring only for keyboard focus (`:focus-visible`).
- Screen readers announce the action through the dynamic `aria-label`; decorative SVGs are hidden from assistive tech.
