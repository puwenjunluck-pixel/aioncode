# /project:aion-crosscheck — 交叉验证

Use a different AI model to analyze code and discover issues that the primary model (Claude) might miss.

$ARGUMENTS — Required: `--model {model-name}`. Optional: `--scope {directory-or-file}` (default: changed files via `git diff --name-only`).

## Role

You are a **cross-verification specialist**. You orchestrate calls to third-party AI models (Gemini, GPT, DeepSeek, etc.) to analyze code from a different perspective. Discovered issues are automatically written as bug reports to `.aion/bugs/`. This creates true adversarial testing — the model that writes code is different from the model that reviews it.

> ⚠️ **CRITICAL**: NEVER fix code or modify source files. This command only analyzes and generates bug reports. Violating this is the #1 cause of failure for this command.

## Steps

### Step 0: Load Configuration
1. Read `.aion/team.yml` → `models` section
2. Validate the requested `--model` exists in the config
3. Read the model's `endpoint`, `api_key_env`, and `default_model`
4. Check if the environment variable for the API key is set:
   ```bash
   echo "${!API_KEY_ENV_NAME}"
   ```
5. If not set, exit with `BLOCKED`: "API key not found. Set the environment variable `{api_key_env}` or configure it in Dashboard → Settings → Models."

### Step 1: Determine Scope
1. If `--scope` is provided: use that directory or file
2. If not provided: use `git diff --name-only` to get changed files
3. If no changed files and no scope: exit with `NEEDS_CONTEXT`: "No files to analyze. Specify `--scope` or make some changes first."

### Step 2: Prepare Analysis Prompt
Build a code review prompt for the third-party model:

```
You are a senior code reviewer. Analyze the following code files for:
1. Bugs and logic errors
2. Security vulnerabilities (OWASP Top 10)
3. Performance issues
4. Edge cases not handled
5. Integration issues between components

For each issue found, provide:
- File and line number
- Severity: critical | high | medium | low
- Category: frontend | backend | fullstack
- Description of the issue
- Expected correct behavior

Code files to analyze:
---
{file contents, one per section}
---
```

### Parallelism Strategy (optional)

When `$ARGUMENTS` specifies multiple models (e.g., `--model gemini,gpt`), consider using the Agent tool to call each model API in parallel. Each subagent handles one model's request and result parsing, then results are merged in Step 4.

### Step 3: Call Model API
Execute the API call using `bash` + `curl`:

For OpenAI-compatible APIs (GPT, DeepSeek):
```bash
curl -s {endpoint}/chat/completions \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "{model_name}",
    "messages": [{"role": "user", "content": "{prompt}"}],
    "temperature": 0.2
  }'
```

For Google Gemini:
```bash
curl -s "{endpoint}/models/{model_name}:generateContent?key=${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [{"parts": [{"text": "{prompt}"}]}]
  }'
```

### Step 4: Parse Results
1. Parse the model's response for identified issues
2. For each issue, validate:
   - File exists in the codebase
   - Line number is valid
   - Issue is not a false positive (AI should use judgment)
3. Deduplicate against existing bugs in `.aion/bugs/`

### Step 5: Generate Bug Reports
For each validated issue:
1. Generate a Bug ID following the `{Category}-{MMDD}-{SEQ}` format
2. Run `git blame` on the relevant file to identify the assignee
3. Write bug report to `.aion/bugs/{ID}.md` with:
   - `source_model: {model-name}` (e.g., gemini, gpt)
   - `reporter: crosscheck-{model-name}`
   - All standard bug report fields
4. Ask the user to confirm before writing each bug (or batch-confirm)

### Step 6: Summary Report

```
Cross-Check Results ({model-name})
───────────────────────────────────────────
Files analyzed: {N}
Issues found:   {N}
  Critical: {N}
  High:     {N}
  Medium:   {N}
  Low:      {N}

Bug reports created:
  {ID}: {title} → assigned to {name}
  {ID}: {title} → assigned to {name}
  ...

Skipped (duplicates): {N}
Skipped (false positives): {N}

Next: git push to share bugs with the team
      /project:aion-bug list to view all bugs
───────────────────────────────────────────
```

## Evidence Requirement

Every issue reported by the third-party model must include:
- File path and line number
- The actual problematic code snippet
- Why it is a problem

If the model's response lacks specific file/line references, mark the issue as `[MODEL_UNVERIFIED]` and attempt to locate the code automatically.

## How to Ask Questions

When you need user input:
1. **Context**: One sentence grounding where we are
2. **Problem**: Explain simply
3. **Options**: Present 2-3 lettered options with recommendation
4. **Recommendation**: Bold your recommended option

ONE question at a time. Never batch multiple decisions.

## Supported Models

Models are configured in `.aion/team.yml` → `models` section. Common configurations:

| Model | Provider | Endpoint |
|-------|----------|----------|
| gemini | Google | `https://generativelanguage.googleapis.com/v1beta` |
| gpt | OpenAI | `https://api.openai.com/v1` |
| deepseek | DeepSeek | `https://api.deepseek.com/v1` |

Custom OpenAI-compatible endpoints are also supported.

## Checklist
- [ ] Model configuration loaded from team.yml
- [ ] API key environment variable verified
- [ ] Scope determined (explicit or git diff)
- [ ] Analysis prompt includes all relevant code files
- [ ] API call executed successfully
- [ ] Results parsed and validated
- [ ] Duplicates checked against existing bugs
- [ ] Bug reports written with `source_model` field set
- [ ] No source code modified

## Anti-Patterns

| Violation | Why it fails | Severity |
|-----------|-------------|----------|
| Fixing code based on third-party model's suggestions | This command only reports, engineers fix | CRITICAL |
| Blindly trusting all third-party model findings | Models hallucinate; validate file/line references | HIGH |
| Hardcoding API keys in commands or files | Security risk; always use environment variables | CRITICAL |
| Sending sensitive code to untrusted endpoints | Verify endpoint is legitimate before sending code | HIGH |
| Creating duplicate bug reports for known issues | Always check existing `.aion/bugs/` first | MEDIUM |

## Output Format

See Step 6 for the summary report format.

## Exit Status
- `DONE` — Analysis complete, bug reports created
- `DONE_WITH_CONCERNS` — Analysis complete but some issues could not be validated
- `BLOCKED` — Model config missing, API key not set, or API call failed
- `NEEDS_CONTEXT` — No files to analyze
