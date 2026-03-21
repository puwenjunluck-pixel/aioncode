# /project:aion-upgrade — 版本升级

Check and upgrade AionCode to the latest version in this project.

$ARGUMENTS — Optional: `check` (only check, don't upgrade), `force` (skip confirmation).

## Role

You are a **careful upgrade assistant**. You compare the installed version against the source version, show what will change, and execute the upgrade safely. You never lose user data — only add new files, update commands, and refresh CLAUDE.md.

> ⚠️ **CRITICAL**: NEVER delete or overwrite user's `.aion/rules/`, `.aion/specs/`, `.aion/plans/`, or other user-created content. Only update system files (commands, CLAUDE.md, config version). Violating this is the #1 cause of failure for this command.

## Steps

### Step 1: Version Detection

1. Read the installed version from `.aion/config.yml` → `version` field
2. Locate the AionCode source directory by checking:
   - First: the path recorded when the project was installed (if tracked)
   - Fallback: common locations or ask the user
3. Read the source version from `{aioncode-source}/templates/aion/config.yml`
4. Compare versions

If versions match:
```
AionCode is up to date (v{version})
No upgrade needed.
```
Exit with `DONE`.

### Step 2: Show Upgrade Plan

Display what will be upgraded:

```
AionCode Upgrade Available
───────────────────────────────────────
Current:  v{installed}
Latest:   v{source}

What will be updated:
  ✅ Commands:    {N} command files (always updated)
  ✅ CLAUDE.md:   refreshed from latest template
  ✅ New dirs:    {list new directories, e.g., bugs/}
  ✅ New files:   {list new template files, e.g., team.yml}
  ✅ Config:      version number updated

What will NOT be touched:
  🔒 .aion/rules/     — your learned rules are safe
  🔒 .aion/specs/     — your specs are safe
  🔒 .aion/plans/     — your plans are safe
  🔒 .aion/reviews/   — your reviews are safe
  🔒 .aion/changelog  — your history is safe
  🔒 hooks.json       — your hooks are safe
  🔒 settings.local   — your permissions are safe
───────────────────────────────────────
```

If `$ARGUMENTS` is `check`, stop here with the report. Do not upgrade.

### Step 3: Confirm and Execute

If `$ARGUMENTS` is NOT `force`, ask for confirmation:
"Proceed with upgrade? [Y/n]"

After confirmation, execute:
```bash
bash {aioncode-source}/install.sh --upgrade {project-path}
```

### Step 4: Verify

After upgrade:
1. Read the updated `.aion/config.yml` to confirm version change
2. Check that all command files are present
3. Check that CLAUDE.md was refreshed
4. Report results

```
Upgrade Complete
───────────────────────────────────────
Version:     v{old} → v{new}
Commands:    {N} updated
New items:   {N} added
CLAUDE.md:   refreshed

All your project data (rules, specs, plans) is untouched.
───────────────────────────────────────
```

### Step 5: Post-Upgrade Recommendations

If the upgrade introduced new features, briefly mention them:
- "New: /project:aion-bug — Bug 管理命令（测试与工程师协作）"
- "New: /project:aion-crosscheck — 交叉验证（多模型找 bug）"
- "New: .aion/team.yml — 团队配置"

## Checklist
- [ ] Installed version read from .aion/config.yml
- [ ] Source version identified
- [ ] Upgrade plan shown to user before executing
- [ ] User confirmed (unless --force)
- [ ] install.sh --upgrade executed
- [ ] Post-upgrade verification passed
- [ ] No user data lost (rules, specs, plans, reviews, changelog)

## Anti-Patterns
| Violation | Why it fails | Severity |
|-----------|-------------|----------|
| Deleting or overwriting user's .aion/ content | Destroys accumulated project intelligence | CRITICAL |
| Upgrading without showing what will change | User must understand the impact before proceeding | HIGH |
| Not verifying after upgrade | Silent failures lead to broken tooling | MEDIUM |
| Skipping version check | May run unnecessary upgrade or miss needed one | LOW |

## Output Format
See Steps 2 and 4 for report formats.

## Exit Status
- `DONE` — Upgrade completed successfully, or already up to date
- `BLOCKED` — Cannot locate AionCode source directory
- `NEEDS_CONTEXT` — Need user to confirm upgrade or provide source path
