# Test Checklist

<!-- Customize this checklist for your project. Used by /aion-test. -->

## Before Generating Tests
- [ ] Existing test files read for patterns and conventions
- [ ] Test framework and directory structure detected
- [ ] Spec acceptance criteria identified (or code-first mode activated)

## Test Quality
- [ ] Tests verify behavior, not implementation details
- [ ] Edge cases cover boundaries and invalid inputs
- [ ] Error paths are tested (every catch/error return)
- [ ] Mocks are at service boundaries, not internal functions
- [ ] Realistic test data used (not "test123" or "foo/bar")

## After Generating Tests
- [ ] Generated tests follow existing naming conventions
- [ ] Tests are in the correct directory
- [ ] All generated tests pass when run
- [ ] Report written to .aion/tests/reports/

## Self-Healing (--heal mode)
- [ ] Spec exists before attempting source code fixes
- [ ] Each healing round logged with [CODE_FIX] or [TEST_FIX] tag
- [ ] Max 3 rounds enforced, max 3 files per round
- [ ] [NEEDS_HUMAN] issues clearly reported, not silently skipped
- [ ] Healed tests re-run and confirmed passing
- [ ] No new test failures introduced by healing fixes

## E2E Testing (e2e mode)
- [ ] Natural language test definitions (.aion/tests/e2e/*.md) parsed
- [ ] Frontmatter validated (feature, target_url, viewport)
- [ ] Given/When/Then structure correctly extracted per TC
- [ ] Playwright MCP availability detected (live vs gen mode)
- [ ] E2E-gen: scripts use semantic locators, no hardcoded selectors
- [ ] E2E-live: screenshots captured at each step
- [ ] E2E-live: adaptive retry on element-not-found (once, 2s delay)
- [ ] Multi-viewport tests generated for each viewport in frontmatter

## Multi-Agent Pipeline (pipeline mode)
- [ ] Analyst output: complete test point inventory with priorities
- [ ] Planner output: P0/P1/P2 test plan with suite grouping
- [ ] Engineer output: test files written following project conventions
- [ ] Sentinel audit: no BLOCK violations remaining
- [ ] Healer output: all tests passing or [NEEDS_HUMAN] documented
- [ ] Intermediate artifacts stored in .aion/tests/pipeline/{feature}/
- [ ] Pipeline report compiled with all stage results
