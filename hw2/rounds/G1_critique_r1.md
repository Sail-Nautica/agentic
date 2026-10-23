# Goldfish 1 critique, round 1 (on E-A v1) — condensed transcription of the agent's report

Verdict: NOT sufficient to build without questions (~10 answers needed). Layout is clear.

## Per-state findings
- Main/Ready: obvious element = Send. Clear icon unspecified (trash vs counterclockwise). Hints should be the focus but have no typography/hierarchy; status line appearing/disappearing makes layout jump (reserve space). Clear sits beside Send at same size (mis-tap risk, patched only by a dialog). "One block per hint" undefined; user's own message is not echoed anywhere.
- Starting: location prompt and game start run in parallel and may look like a hang; placeholder text invites input that cannot be sent; Clear disabled with no Starting timeout means a hung start locks the game; hints placeholder text unspecified.
- Start failed: error in least prominent style (small secondary text); inline Retry vs 44 pt target; empty hints area unspecified; Clear duplicates Retry.
- Sending: stale hints stay visible (looks like nothing happened); typing allowed but Send off is surprising; 30 s timeout may false-fire during Google/Face ID sheets; Return key behavior while Sending unstated.
- Send failed/offline: Retry ambiguous (resend vs restore); restored text collides with a draft typed meanwhile; summary-table Offline row (Send Off, no Retry) contradicts Send-failed row (Send On, Retry); retry after lost reply may double-count a guess.
- Authorizing: surprise Google login right after a winning guess, no explanation; Face ID on every win is heavy; "no biometrics -> passcode only" wording inconsistent with "skip"; Face ID reason text is about the map not account access.
- Google sheet: cancel path ends as a win without map move but state diagram has no such arrow; no retry of the map move after denial; two messages (status line + LLM text) may conflict.
- Face ID: same denied-path gap; "Sign-in cancelled" vs "Authorization cancelled" wording differs; "Set a device passcode to continue" but nothing continues.
- Won/GaveUp: panel (~1/3 screen) may hide the pin; camera should be offset. 5.4 contradicts itself and the state diagram (typed text starts new game vs only button/Clear); fate of typed text unspecified; "I give up" undiscoverable; give up has no visual reveal.
- Clear confirmation: iPad popover unspecified; Play again vs Clear failure paths inconsistent; confirmation arguably unnecessary after the session is over.
- Clearing: keyboard/field behavior unstated; what can fail if Clear is local; map does not return to user.

## Overall gaps
Contradictions: Won/GaveUp typing rule; Offline vs Send-failed rows; Clear icon; denied-auth path to Won; Starting timeout.
Missing: hint definition/count/format/placeholder; echo of user message; Retry semantics and draft merge; timeout pause during system sheets and for Starting; map camera framing/offset/zoom/default region; lat/lon source and bad-coordinate handling; panel visual details; landscape+keyboard room; give-up discoverability; map interactivity vs keyboard dismissal.
Questions: Face ID on every win intended? Pre-sheet explanation before Google? Is sign-in -> Face ID chain clear? Move Clear away from Send? Show pending indicator over stale hints?
Minor: Principle "user sees hints and nothing else" conflicts with congratulation/error text shown in the hints area.
