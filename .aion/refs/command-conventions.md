# Command Conventions

共享约定，所有命令通过 Core Protocol 引用此文件。

## How to Ask Questions

When you need clarification from the user during command execution:
1. State what you've found so far (show evidence, not just conclusions)
2. Present 2-3 concrete options with trade-offs, not open-ended questions
3. Include a recommended default: "If no preference, I'll go with Option A because..."
4. Never ask questions you can answer by reading existing project files
5. Batch related questions — ask once, not repeatedly

## Evidence Requirement

Every assertion must cite evidence:
- Code claims → file path + line number
- Convention claims → source file (eslint config, tsconfig, etc.)
- Performance claims → benchmark or profile data
- Architecture claims → reference to existing patterns in codebase

NEVER make claims like "this is the standard approach" without project-specific evidence.

## Completeness Principle

A task is complete only when:
1. All acceptance criteria from the spec are addressed
2. Edge cases are explicitly handled or documented as out-of-scope
3. The output is self-contained — no implicit "the reader will figure it out"

## Stack Detection

| Indicator | Stack | Test Framework |
|-----------|-------|---------------|
| package.json + tsconfig | Node/TS | jest/vitest/mocha |
| pyproject.toml / setup.py | Python | pytest/unittest |
| go.mod | Go | go test |
| Cargo.toml | Rust | cargo test |
| pom.xml / build.gradle | Java | JUnit/TestNG |
| mix.exs | Elixir | ExUnit |

When detecting stack, read the project's manifest file first. NEVER assume a framework — discover it.
