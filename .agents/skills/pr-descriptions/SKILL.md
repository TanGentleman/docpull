---
name: pr-descriptions
description: >-
  Rules for writing short, plain-English PR descriptions. Read this before you
  write or edit a PR description, or when someone says a PR body is too long or
  sounds like AI.
---

# PR descriptions

A reviewer reads the body to decide if the change is safe to merge. Give them that, and nothing else.

## What to include

1. What changed and why, in one to three sentences. Lead with the result for the user, not with paths or hashes.
2. Behavior conditions or exceptions a reviewer needs to evaluate the change.
3. A link to the related issue, if there is one.
4. Testing: what you ran and what it showed. Say what still needs to be checked.

Most PRs need under 100 words. A one-line fix needs one or two sentences.

## What to leave out

- The same fact under more than one heading ("Problem", "Root cause", "Solution", "Impact").
- Old attempts, pasted test output, and failures already on `main`.
- "What this PR does not do" sections and "not applicable" sections.
- Checkmark lists, bold labels on every bullet, and long agent footers.

## Writing rules

- Keep sentences under 25 words. One idea per sentence.
- Put the condition first: "If the flag is off, the export is uncapped."
- Use simple past, active voice: "Removed the column."
- No hedges (`should`, `may`, `might`) and no filler (`robust`, `comprehensive`, `simply`, `leverage`, `seamless`).
- Write "for example", not `e.g.`. Keep code names, paths, and errors exact.

## Check against the diff

Before you post, compare the description with the diff. Add missing conditions or exceptions that matter. Remove claims the diff does not support. Separate tests you added from tests you ran. Keep the length proportional to the change.

## Example

> Changes to setup scripts no longer require a tool release. The version gate now excludes `web/public/tools/*-init.sh`. Other installer assets stay gated.
>
> **Testing:** Setup-script-only diffs skip the gate. Installer, version, and mixed diffs stay gated.

Adapted from [Corridor: How we deal with slop in PR descriptions](https://www.corridor.dev/research/pr-description-slop).
