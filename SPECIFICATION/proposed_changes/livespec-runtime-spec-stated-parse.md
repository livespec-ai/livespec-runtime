---
topic: livespec-runtime-spec-stated-parse
author: claude-sonnet-5-5:livespec-runtime-2cyhwe
created_at: 2026-11-18T03:40:32Z
---

## Proposal: parse_verdict accepts a verdict wrapped in a single json fence

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md

### Summary

State one clause for `parse_verdict` in `livespec_runtime.spec_stated`: a reply whose JSON verdict sits in a single ```json fence parses to the same verdict as the bare JSON; anything else stays a Failure. Today the ratified contract says a response that is not JSON yields a `Failure` whose error has `field` `None`, and a model reply wrapped in a markdown code fence is not JSON, so a complete, valid verdict is reported as unparseable.

### Motivation

Measured 2026-11-18: 77 of 374 governing-heading judge replies (about 21 percent) on 2026-11-17 and 2026-11-18 were fenced, and each was rejected as an unparseable verdict although it carried a valid verdict. The fixtures, one fenced reply and the same verdict shape as bare JSON, are recorded verbatim in livespec-runtime work item livespec-runtime-2cyhwe. Because the contract names a non-JSON reply a `Failure`, accepting the fence is a genuine contract change rather than a bug fix to implement under the current text. The orchestrator-side companion is orchestrator work item bd-ib-anahvt, cross-referenced in prose only. This proposal is scoped to exactly one clause and changes nothing else about `parse_verdict`.

### Proposed Changes

In `SPECIFICATION/contracts.md` §"Module-level public surface" -> `### livespec_runtime.spec_stated`, in the `parse_verdict` bullet, append one sentence after the sentence ending "...a `detail` naming the parse error.": "A response whose JSON verdict sits in a single ```json fence (an opening line of three backticks and the word json, the verdict, then a closing line of three backticks) MUST parse to the same verdict as the same JSON unwrapped; any other response that is not bare JSON MUST remain a `Failure` as stated above."

In `SPECIFICATION/scenarios.md`, in `## Scenario: parse_verdict names the offending field or the parse error`, append one bullet: "- **And** a response whose JSON verdict sits in a single ```json fence MUST yield a `Success` whose verdict equals the verdict of the same JSON unwrapped, while any other non-JSON response, including one with text outside the fence or with more than one fence, MUST remain a `Failure` whose error has `field` `None`".

The revise that accepts this proposal changes no `## ` heading, so it needs no `tests/heading-coverage.json` row.
