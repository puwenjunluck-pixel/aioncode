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
