# Goldfish 1 critique, round 3 (on E-A v3) — condensed transcription of the agent's report

## Substantive (agent's classification)
1. Q1: no defined "end game" signal; give-up may never reach Ended / Play again.
2. State diagram lacks an arrow for retrying the final request (SendFailed -> Finishing).
3. Recenter tool arguments, end-game tool, and LLM rules text unspecified.
4. Only the latest reply is visible; user cannot review earlier clues or their own guess; sent text survives only as a truncated echo.
5. The failed message is not displayed, so Retry's effect is invisible.
6. 30 s timer runs behind the location prompt and can cause a false StartFailed on first launch.
7. First win forces Google then Face ID with vague "Getting access" copy; Face ID reason "saved sign-in" is inaccurate right after signing in.
8. Play again ranks third and is Footnote-sized; Retry/error text also live in a Footnote row.
9. Return key does nothing when Send is off, with no feedback; field is editable but dead during Authorizing/Finishing.
10. Give-up hint lives only in a long placeholder that truncates and vanishes once typing starts.

## Nitpicks / out of scope
"Clear" vs "New game" naming; Clearing->Starting spinner flicker; dimmed Clear unexplained; action-sheet message not mentioning the answer is lost; location relevance / purpose string; keyboard auto-open; 25 km zoom for all cities; token lifetime length; Clearing error path; muted-text wording variety; Dynamic Type edge cases.

## Other observations
Hierarchy is "map first" while the purpose is "hints first" (partial match). Final-request failure message does not tell the user they won. Token purpose in the game is unexplained to the user.
