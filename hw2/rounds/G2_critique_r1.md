# Goldfish 2 critique, round 1 (on E-A v5 + requirements + preferences) — condensed transcription of the agent's report

Verdict: SUBSTANTIVE. Core requirements covered, but spec contradicts map-dominant and minimal-chrome preferences, leaves the give-up end condition and recenter-on-win only partly met, and carries much unrequested error, timer and accessibility-layout machinery.

## Coverage
Full: map on launch; hints above text box with overwrite; text box + Send enabled rule + progress; Clear wipes + mutual disabling; token flow (Google, Keychain, Secure Enclave, biometric).
Partly: game rule 1 (session end on give-up not modelled; app cannot detect it); game rule 2 (map does not move on denial path); HIG compliance.
Not addressed: /llmclear and "no new endpoints" never mentioned though Clear depends on it. Token lifetime value and what the tool call carries unspecified.

## Contradictions
- Map-dominant: panel allowed up to 45% (60% at accessibility sizes); always-reserved 44 pt status row; 5-line hints; at default size the panel is ~40% so the "cap" is hardly a cap.
- Minimal chrome: Play again, three Retry variants, cancel clause, location notice, compass, pin, placeholders changing in 9 states, confirmation sheet; 10 states for one screen.
- HIG: floating capsule "Clear" is nonstandard and mislabels the restart action (prefer an effect-describing label such as "New game"); permanently reserved empty row; field disabled in 7 of 10 states with placeholders as the status channel (low contrast); muted text low contrast; Play again skips confirmation while Clear confirms (inconsistent).
- Requirements: Clear hidden in Ended departs from "required element visible".
- Internal: principle "app messages live only in the status row" vs messages in placeholders; SendFailed silently drops the failed message when a new one is sent.

## Unrequested features (agent's recommendations)
CUT: Play again button and Ended state (rely on Clear plus the LLM's invitation); StartFailed/SendFailed/FinishFailed/Clearing-failed Retry flows (keep at most one generic retry); offline-vs-unreachable split; timer pause logic and delayed first-launch location request; location-off notice with 5 s dismiss; "Sent:" echo and "Not sent:" mirror (spinner suffices); 4-level status priority and two-part error blocks; accessibility-size layout rules (use system defaults); bespoke cross-fade; draft-preservation machinery; three-way Return rule (Return = Send when enabled); per-state placeholder variants (keep one); FinishFailed bespoke message; duplicate cancel warning (keep Face ID reason only).
KEEP: compass and pin (free MapKit); Clear confirmation (destructive; HIG); Clearing state (needed for the disabling rule, fold text); iPhone-only/real-device scoping; VoiceOver labels and Reduce Motion; one overall timeout so the prototype does not hang.
Marginal: coordinate-range validation; no-passcode handling.

## Other
Map first shows world view then flies (first frame not centered); the "Cancel to skip it" wording invites testers to skip the very feature under test; spec size/complexity (10 states, ~30 strings) is the biggest weakness for a prototype.
