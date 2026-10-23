# Goldfish 3 critique, round 1 (on E-B v2 + design_specs + E-A) — condensed transcription of the agent's report

Verdict: substantive but narrow. Decide Secure Enclave and token lifetime now; verify the "idempotent tool-result resend" and "per-app tool schema" claims before building; simplify the multi-way Retry logic first.

## Coverage
Covered: city fixed and hidden by marker (prompt-only enforcement, admitted); recenter + invite; token via get_auth + ticket into recenter_map (satisfies the spec better than E-A's single tool); back end unchanged, no endpoint/schema change; E-A deviations listed openly (13 rows).
Not accounted: Clearing failure reusing "Couldn't reach the game." (slightly misleading text for a failed wipe); Send disabled in Error with no explanation to the user; tutorial compatibility claimed but not argued.

## Substantive issues
- 2.1 Secure Enclave requirement probably not met: a generic-password item with userPresence is Keychain-protected, not an SE key. Biggest spec risk; decide now (SE-backed P-256 key wrapping the ticket, or an explicit acceptance statement).
- 2.2 Token reuse vs 180 s ticket cap: spec says reusable within lifetime without revalidation; E-B says the back-end ticket expires in 180 s so nearly every win re-runs Google sign-in in sessions over 3 minutes. State what is stored (ticket vs Google credential).
- 2.3 Expiry check: where does expiry live? If inside the userPresence item, the check itself prompts Face ID. Store expiry in plain alongside.
- 2.11 "Harness result update is idempotent" is asserted without evidence; verify in the endpoint or fall back to Clear on any later-leg failure.
- 2.12 / risk 2 "Unknown tool names are forwarded" and "tool schemas stored per app" unverified; does Clear remove stored schemas (stale get_location etc. if the bundle ID is reused)?
- 2.21 Orphan tool call after a leg-1 timeout is not "tiny" with a 30 s timer and slow models.
- Risk 3 Tutorial structure/naming constraint: E-B removes ChatView, role toggle, Game enum and replaces ContentView without mapping new pieces onto tutorial files and names (grading risk); changing Rein.llmTools to return Result alters a tutorial-pattern signature.

## Minor / wording
- 2.4 recenter_map ticket-check sentence is inverted/garbled ("not the one handed out this turn, or expired").
- 2.5 Per-turn memo scope with Retry unclear.
- 2.8 Marker-compliance risk on the weakest runner: flaky starts; mitigation options (strict regex, one silent auto-retry, or manual Retry).
- 2.9 401 plus 422 combo hits the 5-request cap after the user already authenticated.
- 2.15 Keychain delete-then-add: kill between delete and add loses the item (harmless).
- 2.17 Ticket sits in plain text in harness SQLite (note alongside the marker).
- 2.20 Backgrounding during Face ID could end the game as a denial.

## Over-engineering
Per-turn ticket memo; four distinct Retry behaviors (drop resume-from-turn-ID unless idempotence is proven; make Retry after a tool call equal "Clear and restart", Retry of a guess "resend", Retry of a start "wipe then start"); long deviations/risk lists are documentation only.

## Constraint violations
None found (no API/endpoint/format/schema change). Compatibility risks: marker text and tool schemas are stored per bundle ID, so reusing a tutorial bundle ID collides.
