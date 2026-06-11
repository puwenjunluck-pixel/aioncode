# Write Protocol

<!-- 被多个 skill 跨目录引用（plan/commit/save/scan/fix/qa），勿移动或重命名 -->

Commands that write to `.aion/` MUST follow this protocol. Before ANY write operation, determine the target file's category and apply the corresponding rules.

> **Enforcement**: Violating a Refusal Condition means the write MUST NOT proceed. Terminate the write operation and report the violation to the user.

## Categories

### Accumulative (append-only)

**Files**: `rules/*.md`, `changelog.md`
**Commands**: review, commit, save

**Rules**:
1. Always APPEND to existing content. Never overwrite or replace existing entries.
2. Before appending, READ the target file and search for semantic duplicates.
3. If duplicate found → skip the entry, inform the user.
4. If extends existing entry → update that entry in-place.
5. If conflicts with existing → flag to user, do NOT auto-write.

**Refusal Condition**: If the target file was not read before writing (i.e., deduplication search was not performed), this write is INVALID. Terminate and report: "Write refused: Accumulative target not read for dedup check."

---

### Versioned (design artifacts with history)

**Files**: `specs/*.md`, `plans/*.md`
**Commands**: think, plan, save, scan（`specs/_product.md` 由 scan 以 Versioned 写）

**Rules**:
1. Before writing, check if a file with the same name exists in the target directory.
2. If no existing file → create as v1.
3. If existing file found → read it fully, then:
   - **A) New version** (recommended): archive current as `{name}.v{N}.md`, write new with `version: {N+1}`, require `change_reason` from user.
   - **B) Overwrite**: user explicitly accepts losing history.
   - **C) New file**: use a different filename.
4. Max 10 archived versions per file. Warn at limit.

**Scope conflict detection**:
- Versioned files MUST declare `scope` in frontmatter: `api | web | mobile | infra | full`
- Same name + same scope → normal version check (A/B/C)
- Same name + different scope → **force option C**, auto-suggest `{name}-{scope}.md`

**Stale file warning**:
- Before modifying a Versioned file, check its `author` and git last-modified date.
- If `author` differs from current user AND last modified > 2 days ago → warn:
  "Warning: This file was last modified by {author} {N} days ago. Consider `git pull` first. Continue? [Y/n]"

**Frontmatter standard**:
```yaml
---
version: {N}
author: {from team.yml or "unknown"}
scope: {api|web|mobile|infra|full}
change_reason: "{reason, null for v1}"
created_at: {YYYY-MM-DD}
---
```

**Refusal Condition**: If an existing file was found but no Diff Summary (what changed between old and new) was presented to the user, this write is INVALID. Terminate and report: "Write refused: Versioned file exists but no diff summary provided."

---

### Regenerable (derived from analysis)

**Files**: `refs/*`, `tests/e2e/*`, `contracts/*`, `checklists/*`
**Commands**: scan, qa

**Rules**:
1. On first creation, append a fingerprint comment at end of file:
   `<!-- aion:fingerprint:{MD5_OF_CONTENT} -->`
   (MD5 is computed on the file content EXCLUDING the fingerprint line itself)
2. Before regenerating an existing file, read it and extract the fingerprint.
3. Compute MD5 of the current file content (excluding fingerprint line) and compare:
   - **Hash match** → file unmodified by user. Safe to regenerate silently. Update fingerprint.
   - **Hash mismatch** → file was modified by user. Switch to Versioned strategy: show diff, ask user to confirm (Update / Keep existing / Replace).
   - **No fingerprint found** → legacy file, treat as user-modified. Ask before overwriting.

**Refusal Condition**: If an existing Regenerable file was not read and its fingerprint was not checked before writing, this write is INVALID. Terminate and report: "Write refused: Regenerable file exists but fingerprint not verified."

---

### Unique-by-ID

**Files**: `bugs/{BUG-ID}.md`, `reviews/{feature-name}.md`
**Commands**: qa, review

No additional write protection needed. ID/name guarantees uniqueness by design.

---

## Quick Reference

| Category | Read before write? | User confirm? | Fingerprint? | Version? |
|----------|-------------------|---------------|-------------|----------|
| Accumulative | YES (dedup) | No (auto-append) | No | No |
| Versioned | YES (diff summary) | YES (A/B/C) | No | YES |
| Regenerable | YES (fingerprint) | Only if modified | YES | No* |
| Unique-by-ID | No | No | No | No |

*Regenerable files that were user-modified are promoted to Versioned strategy for that write.
