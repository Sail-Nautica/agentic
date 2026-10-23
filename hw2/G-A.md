# Exhibit G-A: UI/UX Critic Summary (Goldfish 1, Principal Native Mobile UI/UX Developer)

Goldfish 1 saw only the UX spec (E-A), never the design requirements, and was asked per state for purpose, main control, visual ranking and confusing items, plus whether the spec could be built without questions. Five fresh sessions reviewed five successive drafts (v1 to v5).

**Round 1 (v1).** Verdict: not buildable. Found contradictions (the end-of-game state described two ways; offline and send-failed rows disagreeing), an unpicked Clear icon, no definition of what a hint is, no echo of the user's message, a layout that jumps when the status line appears, Clear placed beside Send, and a surprise Google sheet right after a winning guess.

**Round 2 (v2).** About 85% buildable. Remaining: which status message wins when several apply, whether the 30 s timer pauses under the location prompt, whether the fly-to repeats in game 2, missing placeholders, an unspecified Return key, "Signing in" copy wrong when only Face ID appears, and Clear versus Play again duplication.

**Round 3 (v3).** Found that the give-up signal depended on an undecided "end game" tool, a missing retry arrow for the final request, an invisible failed message, a timer that could false-fire behind the location prompt, vague sign-in copy, and small, hard-to-notice Retry and Play again buttons. The product owner then decided against an end_game tool, so give-up became undetectable and Clear its only restart.

**Round 4 (v4).** Reviewer said the UI was unusually complete; the gaps it listed were mostly technical-design matters (tool schema, token purpose, system prompt), which were deferred to Exhibit E-B. In-scope fixes: a warning that cancelling skips the map move, consistent handling of discarded closing text, large-text fallback, pin framing, and clearer Clear confirmation wording.

**Round 5 (v5).** Remaining findings largely restated accepted product decisions (a given-up game looks like Ready; two back-to-back prompts on a first win; no cancel for a slow request; Play again without confirmation) or were polish. One genuine defect was carried forward: the Clearing failure path cannot occur for a local wipe and should be removed. Review closed here; v5 passed to Goldfish 2.

**Net effect.** E-A grew from a loose layout sketch into a complete state table with fixed layout rules, one status row with a priority order, per-state placeholders, retry semantics that cannot double-count a guess, and an honest list of accepted trade-offs.
