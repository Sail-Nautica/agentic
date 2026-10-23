# Goldfish 1 critique, round 2 (on E-A v2) — condensed transcription of the agent's report

Verdict: ~85% buildable as-is; remaining substantive items are state-edge decisions, not structural problems.

## Substantive
- Status row can need two messages at once (location-off vs start spinner; "Map not moved." + Play again; echo + pending). No priority order; no wrapping rule at large Dynamic Type.
- 30 s timer during the location-permission alert: running or paused?
- Map on game 2 restart: does the launch fly-to to the user repeat? What counts as "user touched the map"?
- Placeholders for non-Ready field states promised in section 3 but never listed in section 6.
- Stuck win: if the LLM never calls the tool, only Clear escapes.
- Return key behavior when Send is disabled (empty field, Sending, Authorizing).
- "Signing in" copy is wrong when only Face ID appears.
- Clear vs Play again duplicate in Ended; Clear label/VoiceOver name ("start over") and confirmation sheet button ("Clear") vs title ("Start a new game?") mismatch.
- Hints area content in StartFailed ("last text if any") and Clearing ("empty") conflicts with the placeholder rule.
- Status row during the follow-up request after the tool result (does "Sent: ..." return?).
- How "offline" is distinguished from "couldn't reach".

## Nitpicks / out of scope
Colors, radii, animation timings, Google "unverified app" warning, Clearing flicker, cross-fade details, VoiceOver wording, Reduce Motion details, 25 km framing, compass vs Clear overlap on small phones, map visual weight, hint dimming, large-type panel height.
