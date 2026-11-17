from __future__ import annotations

from collections.abc import Callable
from enum import IntEnum, auto
from typing import Annotated

from msgspec import Meta, Struct, json

# msgspec copies Meta's description verbatim into the schema's description.
class CompletionSummary(Struct, forbid_unknown_fields=True):
    completion: Annotated[str, Meta(description="The complete response text for the user.")]
    summary: Annotated[
        str,
        Meta(
            description=(
                'A concise, deanaphorized summary for semantic retrieval: restate '
                'what the user asked and what was concluded, using the explicit '
                'entity and topic names that appear in the conversation. No '
                'pronouns (it, they, this, that) and no back-references — every '
                'sentence must make sense alone, as a standalone record in a '
                'vector store. Only names actually present in the conversation; '
                'no invented entities, no boilerplate framing ("The user asked '
                'about... and the assistant explained...").'
            )
        ),
    ]

def _completionSummaryResponseFormat() -> bytes:
    schema = json.schema(CompletionSummary)
    schema.pop("$schema", None)
    schema.pop("title", None)
    envelope = {
        "type": "json_schema",
        "json_schema": {"name": "completion_summary", "strict": True, "schema": schema},
    }
    return json.encode(envelope)

structuredResponseFormat = _completionSummaryResponseFormat()

class LexPhase(IntEnum):
    ObjectStart = auto()  # expect '{'
    Key = auto()          # expect opening '"' of a property name
    KeyName = auto()      # capturing property-name bytes
    Colon = auto()        # expect ':' after a property name
    Value = auto()        # expect the value's opening '"'
    InString = auto()     # inside a string value; target classifies spans
    AfterValue = auto()   # expect ',' (next property) or '}' (end)
    Done = auto()

class LexTarget(IntEnum):
    Completion = auto()
    Summary = auto()

type LexSink = Callable[[LexTarget, str], None]

_LEXER_KEY_CAP = 16

class CompletionLexer:
    __slots__ = ("phase", "target", "inEscape", "key", "completionSeen",
                 "summarySeen", "fallback")

    def __init__(self):
        self.phase = LexPhase.ObjectStart
        self.target = LexTarget.Completion
        self.inEscape = False
        self.key: list[str] = []
        self.completionSeen = False
        self.summarySeen = False
        self.fallback = False

    # Shared-transition table: accepted character(s) → next phase, plus an
    # optional pre-transition hook run before the phase assignment. Stored
    # unbound — hooks are called as hook(self).
    _TRANSITIONS = {
        LexPhase.ObjectStart: ({'{': LexPhase.Key}, None),
        LexPhase.Key:         ({'"': LexPhase.KeyName}, lambda self: self.key.clear()),
        LexPhase.Colon:       ({':': LexPhase.Value}, None),
        LexPhase.Value:       ({'"': LexPhase.InString}, lambda self: setattr(self, "inEscape", False)),
        LexPhase.AfterValue:  ({',': LexPhase.Key, '}': LexPhase.Done}, None),
    }

    def feed(self, fragment: str, sink: LexSink) -> str | None:
        i = 0
        while i < len(fragment):
            match self.phase:
                case (
                    LexPhase.ObjectStart
                    | LexPhase.Key
                    | LexPhase.Colon
                    | LexPhase.Value
                    | LexPhase.AfterValue
                ):
                    ch = fragment[i]
                    if ch in ' \t\n\r':
                        i += 1
                    else:
                        targets, hook = self._TRANSITIONS[self.phase]
                        nxt = targets.get(ch)
                        if nxt is None:
                            return self._latch(fragment, i)
                        if hook: hook(self)
                        self.phase = nxt
                        i += 1

                case LexPhase.KeyName:
                    # residue must start at the key's opening quote; a key that
                    # began in an earlier fragment (or overran the cap) clamps
                    # to the fragment start — best effort
                    from_ = max(i - len(self.key) - 1, 0)
                    if fragment[i] == '"':
                        if not self._resolveTarget():
                            return self._latch(fragment, from_)
                        self.phase = LexPhase.Colon
                        i += 1
                    else:
                        if len(self.key) >= _LEXER_KEY_CAP:
                            return self._latch(fragment, from_)   # oversized key
                        self.key.append(fragment[i])
                        i += 1

                case LexPhase.InString:
                    spanStart = i
                    closed = False
                    while i < len(fragment):
                        if self.inEscape:
                            self.inEscape = False
                            i += 1
                            continue
                        atBackslash = fragment.find('\\', i)
                        atQuote = fragment.find('"', i)
                        at = atBackslash if atQuote == -1 else atQuote if atBackslash == -1 else min(atBackslash, atQuote)
                        if at == -1:
                            i = len(fragment)
                            break
                        if fragment[at] == '\\':
                            self.inEscape = True
                            i = at + 1
                        else:
                            self._emit(spanStart, at, fragment, sink)
                            self.phase = LexPhase.AfterValue
                            i = at + 1
                            closed = True
                            break
                    if not closed:
                        self._emit(spanStart, i, fragment, sink)

                case LexPhase.Done:
                    i = len(fragment)
        return None

    # Closing quote seen, determine if it closes a "completion" or "summary"
    def _resolveTarget(self) -> bool:
        match "".join(self.key):
            case "completion" if not self.completionSeen:
                self.target = LexTarget.Completion
                self.completionSeen = True
                return True
            case "summary" if not self.summarySeen:
                self.target = LexTarget.Summary
                self.summarySeen = True
                return True
            case _:
                return False

    # fallback triggered/latched on violation:
    def _latch(self, fragment: str, start: int) -> str:
        self.fallback = True
        return fragment[start:]

    def _emit(self, start: int, end: int, fragment: str, sink: LexSink) -> None:
        if start >= end: return
        sink(self.target, fragment[start:end])

def _pushEscape(ch: str, frame: list[str]) -> None:
    match ch:
        case 'n': frame.append('\n')
        case 'r': frame.append('\r')
        case 't': frame.append('\t')
        case '"': frame.append('"')
        case '\\': frame.append('\\')
        case '/': frame.append('/')
        case 'b': frame.append('\b')
        case 'f': frame.append('\f')
        case 'u': frame.append('\\u')
        case _: frame.append('\\'); frame.append(ch)

def escapeFrame(span: str, frame: list[str], pending: bool) -> bool:
    rest = span

    if pending:
        # an empty span must not consume the withheld backslash
        if rest:
            _pushEscape(rest[0], frame)
            rest = rest[1:]
            pending = False

    while (at := rest.find('\\')) != -1:
        frame.append(rest[:at])
        if at + 1 < len(rest):
            _pushEscape(rest[at + 1], frame)
            rest = rest[at + 2:]
        else:
            return True

    frame.append(rest)
    return pending

class Capture:
    def __init__(self) -> None:
        self.text: list[str] = []
        self.pending = False

    def push(self, span: str) -> None:
        self.pending = escapeFrame(span, self.text, self.pending)

    def flushPending(self) -> bool:
        if not self.pending:
            return False
        self.text.append("\\")
        self.pending = False
        return True
