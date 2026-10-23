## One-page summary of E-A (UX spec)

**What it is.** A one-screen iPhone prototype: a full-bleed map, a compact bottom panel (hints, one status row, a guess field with Send), and a floating Clear button at top-left. Nothing else is on screen except four system overlays: the Clear confirmation, the location prompt, the Google sign-in sheet and the Face ID prompt.

**How it behaves.** On launch the map starts on a default view and moves to the user once a location fix arrives. The app sends the game rules and the LLM silently picks the city. The panel shows only the latest LLM reply; a new reply replaces the old one. Send is enabled only with text and only when idle. While Sending or Clearing, the other control is off. Six states cover everything: Starting, Ready, Sending, Error, Ended, Clearing. A single status row shows a spinner message, one error with one Retry button, or the Play again button.

**Winning.** When the LLM calls the recenter tool the app asks for sign-in (Google, only if no unexpired token) and Face ID, then flies the map to the city and drops a pin. If either is cancelled the map does not move and the LLM reveals the city in text. After a win the field is disabled and Play again appears.

**Decisions fixed by the owner.** Giving up is a typed phrase; there is no end-game tool, so the app cannot detect a give-up and the restart is Clear. Biometrics on every token read. Clear always confirms. The status row stays reserved so nothing jumps.

**How it changed.** Seven drafts. The first was loose and had contradictions; the middle drafts added a full state table and many error cases; the auditor round then cut it to about half its length and six states, to fit the "map-dominant, minimal chrome" preference.
