---
topic: old-owner-refs-livespec-ai
author: claude-sonnet-5-5
created_at: 2026-11-16T18:48:04Z
---

## Proposal: repoint-old-owner-references-to-livespec-ai

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md

### Summary

Repoint the four live-spec references that name the old GitHub owner thewoolleyman to the livespec-ai organization.

### Motivation

The fleet moved to the livespec-ai GitHub organization. Plan stale-base-merge-options (epic livespec-dev-tooling-xowhol) DoD assertion 7 requires zero graded references to the old owner in committed master trees. The affected text is live SPECIFICATION text, so it moves through propose-change and revise rather than a direct edit.

### Proposed Changes

In SPECIFICATION/contracts.md, change both `https://github.com/thewoolleyman/livespec-runtime.git` pins (the dependency-group and runtime-dependency examples, near lines 1046 and 1058) to `https://github.com/livespec-ai/livespec-runtime.git`. In SPECIFICATION/scenarios.md, change `https://github.com/thewoolleyman/livespec` to `https://github.com/livespec-ai/livespec` (lines 10 and 104), `https://github.com/thewoolleyman/livespec-runtime` to `https://github.com/livespec-ai/livespec-runtime` (line 19), and `git@github.com:thewoolleyman/livespec.git` to `git@github.com:livespec-ai/livespec.git` (line 119). No other text changes.
