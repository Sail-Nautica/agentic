# Elephant notes after v6 (not shown to Goldfish)

## Not adopted from G2 round 1
1. Removing Ended / Play again: product-owner decision; question 1.
2. Removing the reserved status row: product-owner decision; shrunk to one line (44 pt).
3. Renaming the button to "New game": requirements name a "Clear button"; sheet and VoiceOver describe the effect (question 2).
4. Dropping the Clear confirmation: auditor agreed to keep it; only guard after an undetectable give-up.
5. Hiding Clear in Ended: reversed; stays visible.
6. Delayed first-launch location request and timer pause logic: cut. Cost: one possible false start failure on first launch, fixed by Retry.
7. Echo of sent/failed text, offline-vs-unreachable split, location notice, cancel clause in status row, extra placeholders, large-text layout rules, cross-fade, draft handling: cut.
8. Separate StartFailed/SendFailed/FinishFailed/Clearing-failure flows merged into one Error + Retry; Clearing failure removed.

## Questions for the product owner
1. Keep both Play again and Clear in Ended, or drop Play again?
2. Visible label "Clear" or "New game"?
3. Is a possible false start error on first launch (location prompt over the first request, fixed by Retry) acceptable, or delay the first-launch location request?
4. Is the LLM API stateless, app holds history?
5. Testers on a physical iPhone with passcode + biometrics, on the Google test-user list?
