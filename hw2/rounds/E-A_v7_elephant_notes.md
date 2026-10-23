# Elephant notes after v7 (not shown to Goldfish)

## Not adopted from G2 round 2
1. Removing panel-aware pin framing: one sentence, makes the win visible above the panel.
2. Removing the pin: marks the city on a map that may be zoomed or rotated; free.
3. Removing the lat/lon range guard: one check; protects the map from a bad tool argument.
4. Dropping Play again, the reserved status row, or the visible "Clear" label: product-owner decisions.
5. Delaying the first-launch location request: product owner accepted the false-error risk.
6. "Map not moved." message, echo of sent text, dimming of old hints, held-guess handling: cut.
7. Special large-text layout rules: system scaling plus "hints scroll first" is enough.

## Questions for the product owner
1. Smallest iPhone model testers might use?
2. Is the LLM API stateless, app holds history?
3. Testers on physical iPhones with passcode + biometrics, on the Google test-user list?
