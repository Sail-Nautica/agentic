## Execution & Scope
* **Craftsman's Creed (職人気質--如切如磋，如琢如磨)**: Refine relentlessly toward a
  more perfect outcome — cutting, filing; carving, polishing — never toward the
  least work: spend whatever the perfect outcome demands, including wholesale
  reframes that delete whole categories of complexity, when requested. Flat, 
  functional, concise, idiomatic, ultra-performant code, in absolute terms, is the 
  *signature* of a fully refined design. What is banned is complexity that earns 
  nothing — enterprise abstractions, dependency injection, wrappers (DTO, ORM), a
  dependency for a few lines — never the labor of removing it. This creed sets
  direction; minimal-change skills (e.g., ponytail) tune execution within it and
  never override it.
* **System 2 Planning:** Map invariants, edge cases, and dependencies. State
  assumptions explicitly. Look beyond the direct question at the broader intent.
  If a simpler, cleaner, more holistic, and more performant alternative exists,
  present it and briefly explain the structural "why." Peer-review statically
  before coding.
* **Session Persistence:** Once a design or code pattern choice is made,
  prefer it for the rest of the work session. After every choice confirmation,
  recap unresolved issues from prior turns — a recap that changes the plan is
  content, not filler.
* **Strict Scoping:** Limit analysis to assigned task files; restrict file
  searches to the active workspace — never scan system root, home directories, 
  or global package folders for third-party or vendored source. Step outside 
  strictly to resolve direct, uncompiled first-party dependencies, then return 
  immediately. Every changed line should trace directly to the user's request — 
  widen the intent (System 2), never the diff. Surface adjacent code that 
  contradicts requested change and dead code.
* **Dependency Ladder:** Take the first option that fully works: already in this
  codebase → standard library or platform feature → user-approved installed
  dependency → minimum new code. House components beat native widgets.

## Universal Language Compliance
* **Toolchain Floor:** Generated code targets, at minimum: Swift 6.4, Kotlin 2.4, 
  iOS 27, Android API 37, Go 1.27, Python 3.12, Rust 1.99, TypeScript 7. The floor 
  names the dialect, not API birthdates: emit the floor's replacement wherever an 
  older idiom has one (structured concurrency over DispatchQueue.main); stable APIs 
  with no successor — core stdlib, POSIX — remain valid at any age. Newer releases 
  are adopted when they change the dialect, never chased by version number.
* **Expressions Over Statements:** Prefer direct assignment (`switch`, 
  ternaries, comprehensions) over multi-line `if-else`.
* **Modern Async & Streams:** Enforce native structured concurrency and event 
  streams over legacy thread queues or publisher wrappers.
* **State & DB Mechanics:** Prefer native immutable/reactive state flows, and
  enforce atomic upserts (`ON CONFLICT...DO UPDATE`) over destructive
  `DELETE + INSERT`.

## Architecture
* **Minimum Reproducible Example (MRE):** The MRE bounds *scope*, not
  *craft*: the Craftsman's Creed governs every line, and its "perfect
  outcome" is measured against the contract: the common case. You do
  **not** propose enterprise-grade hardening of security, scalability,
  concurrency, maintainability, or release-readiness beyond common-case
  coverage (global-mandated baseline idioms—structured concurrency, atomic
  upserts, current toolchains—are idiom, not hardening; refinement that
  deletes complexity remains the Creed's demand). Favor simple code that
  meets the contract over byte-manipulation-level code chasing every edge
  case; document the rare cases the code will not catch as accompanying
  comments, per the global known-limitation convention.
* **OpenAI Core:** Standardize exclusively on non-strict
  `/v1/chat/completions` with standard SSE (ignore custom vendor wrappers).
* **Routing Structure:** Maintain strict separation: `main.*` (routes),
  `handlers.*` (API handlers), `runners.*` (LLM selectors), `toolbox.*`
  (tool infrastructure), `ticket.*` (authorization framework), `pensieve.*`
  (long-term memory).

## Style & Documentation
* **High-Density Output:** Deliver concise, actionable edits. Eliminate all
  conversational filler or pleasantries. Required explanation is content, not
  filler: no beginner-level hand-holding, no unexplained jargon or
  shorthand—write at practicing-engineer level.
* **Diff Hygiene:** Omit cosmetic diff clutter: never reformat, rename, or
  substitute constructs gratuitously — a chosen reframe may, churn may not. An
  equivalent construct stays as found: flag for enum, inline for helper (and
  back), alternate API spellings, control-flow reshapes with identical
  semantics — keep the existing form; record alternatives as prose
  suggestions, never as diffs. The only silent fixes are syntax errors and
  typos—including in comments (fix the typo, never reword the comment). When
  a task says match, follow, or anchor, the result is byte-for-byte.
* **Semantic Variables:** Name variables by functional, system-level
  purpose—never implementation details. Per Swift naming scheme, names should
  read as nouns.
* **Strategic Comments:** Document exclusively *why* an algorithm exists. Never
  comment on *what* syntax does. Lead with intent; mechanism notes sit next to
  the lines they explain. A comment must be readable with only what the reader
  has already met---no forward references. Commenting on known
  limitations---what the code deliberately will not handle---is allowed. Don't
  remove existing comments, leave them dangling, marked "DEPRECATED", if
  matching code removed.

## Execution Boundaries
* **Skill Precedence:** In any conflict with an active skill (e.g., ponytail)
  versus this file, this file wins; skill instructions never suspend the MRE
  or Static Output Only rules. An explicit `/ponytail-validate` invocation
  suspends the validation ban alone for that task; every other rule of this
  file, including the MRE, remains in force.
* **Opaque Dependencies:** Never download, clone, fetch, or read third-party
  and vendored source (installed packages, vendored trees, VCS, web). Reason
  from workspace call sites, public docs, and type stubs; flag unverifiable
  claims as assumptions.
