# Goldfish 2 critique, round 3 (on E-A v7 + requirements + preferences) — condensed transcription of the agent's report

Verdict: remaining critique mostly MINOR. One substantive item (give-up) is a product-owner decision.

## Coverage
Full: hints above text box; Send rule and progress; Clear wipe and mutual disabling; rule 2 (tool + Play again as the invitation); rule 3 token flow; no new endpoints beyond /llmclear; no enterprise extras.
Mostly: map centered at launch (first frame is the default view; owner decision 0(b)); game rule 1 (give-up ends only in LLM text, owner decision 0(c)); "elements fully visible" (keyboard and large-text cases left to on-device verification).
Partly: HIG.

## Contradictions (all noted, none new)
Map-dominant vs ~1/3 panel with a reserved status row and 2-line hints minimum; keyboard-up panel exceeds 1/3; status row "one line" would truncate at large Dynamic Type (HIG says wrap); destructive button "Clear" vs title "new game" vocabulary mismatch; passcode fallback relaxes "biometric check" (owner decision; Keychain access flag could be biometric-only); first frame not centered (owner decision).

## Unrequested features
Retry/Error, 30 s timeout, Clear confirmation, Play again, range guard: justified. Play again duplicates Clear in Ended: weakest justified item, keep. Pin: borderline, cheap.

## Other discrepancies
Give-up flow inconsistent: user may keep playing against a revealed city (admitted; owner decision). Denial reveals the city so the sign-in step is bypassable by cancelling (owner decision). Final-request Retry defined only in prose. Dangling tool call if the user sends new text after a failed final request (harness may reject; belongs to technical design). String count error: five status messages, not four. Panel "one third" unverified on small phones.

## Agent's own remaining changes
(a) fix string count; (b) say whether the status row wraps at large text and keep buttons visible; (c) specify what Retry/new Send does after a failed final win request; (d) consider cutting the pin.
