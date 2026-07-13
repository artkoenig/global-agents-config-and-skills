---
name: code-generation-principles
description: MANDATORY FOR IMPLEMENTATION. This skill MUST be read and applied BEFORE writing, editing, generating, or refactoring any code files or unit tests.
user-invocable: false
---

# Code Generation Principles

For code generation, follow these principles:

- **Meaningful Names:** Use clear, unambiguous identifiers for variables, functions, and classes.
  The intent must be immediately recognizable; cryptic abbreviations are prohibited.
- **Single Responsibility Principle (SRP):** Every class and function must have exactly one clearly defined responsibility.
- **Short Functions & Single Level of Abstraction:** Keep functions compact.
  Within a function, handle only a single level of abstraction.
- **No Magic Values:** Avoid hardcoded numbers or strings in code.
  Instead, use named constants, enums, or configuration files.
- **Minimize Side Effects:** Functions should be pure whenever possible, deliver deterministic results, and avoid modifying unexpected global states.
- **Self-Explanatory Code Over Comments:** Use comments sparingly.
  Code must be readable and self-explanatory through good structure and naming conventions (exception: documentation of complex business logic or public APIs).
- **DRY Principle (Don't Repeat Yourself):** Consistently avoid code duplication.
  Extract redundant code into reusable components.
- **Robust Error Handling:** Handle exceptions explicitly and meaningfully.
  Errors must never be silently swallowed (no empty `catch` blocks).
- **Comprehensive Unit Tests:** Secure code directly with isolated, fast, and meaningful tests (FIRST principle: *Fast, Independent, Repeatable, Self-Validating, Timely*).
- **YAGNI Principle (You Aren't Gonna Need It):** Do not write code for hypothetical, future requirements.
  Only implement what is currently needed.
- Never manually modify any files that are marked as auto-generated.
