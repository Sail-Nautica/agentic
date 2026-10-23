# Goldfish 2 critique, round 2 (on E-A v6 + requirements + preferences) — condensed transcription of the agent's report

Verdict: SUBSTANTIVE (smaller than round 1). Required elements covered; center-on-launch and session-end only partly met; permanent panel works against map-dominant; some unrequested state machinery remains.

## Coverage
Full: hints above text box with overwrite; Send enable rule and progress; Clear wipe and mutual disabling; token flow on paper; /llmclear-only constraint (5.5.3).
Partly: map centered at launch (starts on default view then moves once; stays default if location denied, no notice); game rule 1 (give-up never formally ends the session); game rule 2 (invite to play again is a fixed button rather than the LLM's invitation; map does not move on denial); "every element fully visible, non-overlapping" (claimed, not backed at large text sizes / keyboard up on small phones); exclusion of extras; HIG.

## Contradictions
- Reserved 44 pt status row + 2-line hints minimum is a large fixed block, against map-dominant (justified only to avoid layout jump).
- Keyboard up plus one-third panel leaves little map on small phones; "at most one third" cannot be guaranteed at large Dynamic Type while "no special large-text layout".
- "Clear" label may read as clearing the text box (requirement names the control; defensible).
- Clear/Play again skip confirmation in Ended but Clear confirms in Ready: same button, different behavior by state.
- One-line status row with message + spinner + button may truncate at larger text sizes.
- Field disabled in Ended while placeholder invites "give up"; give-up phrase only discoverable via placeholder that vanishes when typing starts.
- Field editable during win flow / Starting / Clearing while sheets appear (minor).
- Principle "app messages live only in the status row" is too strong (Face ID reason string and confirmation dialog also carry app messages); header "one screen, nothing else" omits the action sheet as an overlay.

## Unrequested features (agent's recommendations)
CUT: held-guess logic and distinct retry kinds (show message; let user resend or Clear); "Map not moved." message; skip-confirmation branch on Clear/Play again (always confirm or never); dimming old hints (spinner is enough); panel-aware pin framing and 2 s animation polish (plain recenter acceptable); six status strings / floating-material polish (trim).
KEEP: single simple 30 s timer; Return = Send; tap map to dismiss keyboard; compass; lat/lon range guard; scroll for long hints; pin (flag as extra).
Flag: Play again vs Clear duplication in Ended (keep one or avoid different behaviors); passcode fallback weakens "biometric check" wording (state as deliberate relaxation or remove); known first-launch false timeout should be fixed (delay first request) rather than accepted (owner chose to accept).

## Other discrepancies
Stuck win if LLM forgets the tool (admitted); denial path reveals the city without a successful win flow (state as a decision); Keychain/Secure Enclave details are implementation notes inside a UX spec; Clear disabled in Starting with 30 s hang means no escape; closing text may duplicate the Play again invitation.
