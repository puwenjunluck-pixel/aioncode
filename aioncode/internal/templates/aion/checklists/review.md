# Review Checklist

<!-- Customize this checklist for your project. Used by /aion-review. -->

## Completeness
- [ ] All changed files reviewed (none skipped)
- [ ] Spec acceptance criteria verified
- [ ] Plan verification strategy checked

## Code Quality (40%)
- [ ] Readable and maintainable
- [ ] DRY — no unnecessary duplication
- [ ] Appropriate abstractions (not over/under-engineered)

## Security (30%)
- [ ] No injection vulnerabilities (SQL, command, XSS)
- [ ] No hardcoded secrets or credentials
- [ ] Authentication/authorization properly handled
- [ ] Input validation at system boundaries

## Architecture (30%)
- [ ] Follows plan design decisions
- [ ] Consistent with existing codebase patterns
- [ ] Interface contracts respected (.aion/contracts/)
- [ ] No unnecessary breaking changes

## Rule Extraction
- [ ] Patterns worth remembering identified
- [ ] Existing rules checked for duplicates
- [ ] New rules are actionable + specific + evidenced
