# Elephant notes after v3 (not shown to Goldfish)

## Not adopted from G1 round 2
1. Network-reachability monitor / pre-send check: error type is enough.
2. Cancel button for slow requests: bypasses Send/Clear rules; 30 s timeout is the limit.
3. Auto-detecting a stuck win: LLM owns game logic; Clear is the escape.
4. Retry for map move after denial, transcript view, explainer screen before Google sign-in.
5. Landscape and iPad.
6. Per-state Clear variants such as undo.

## Open questions for the product owner
1. Ending signal: add one more LLM tool, "end game" (no args, no auth), called after a correct guess (after recenter result) or give-up? Without it the app cannot show Ended after give-up.
2. Is the LLM API stateless, app holds history?
3. 30 s, 5 km launch, 25 km win acceptable?
4. Testers on a physical iPhone with passcode + biometrics, on the Google test-user list?
