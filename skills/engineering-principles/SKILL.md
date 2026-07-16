---
name: engineering-principles
description: MANDATORY FOR DESIGN AND IMPLEMENTATION. This skill MUST be read and applied BEFORE making architectural decisions, choosing libraries/patterns, defining component boundaries, or doing cross-module refactoring, AND BEFORE writing, editing, generating, or refactoring any code files or unit tests.
user-invocable: false
---

# Engineering Principles

## Architecture & Design

For architectural decisions or cross-module refactoring, follow these principles:

### 1. State Management

- **Unidirectional Data Flow (UDF):** Data moves strictly in one direction (e.g., state flows down to the UI, events flow up to logic) to keep the system state deterministic.
- **Single Source of Truth (SSOT):** Every state exists in only a single, clearly defined place.
  Avoid redundant or synchronized states.
- **Immutability:** Data structures and states should be defined as immutable by default.
  Changes produce new instances instead of mutating existing objects.

### 2. Extensibility & Modularity

- **Open/Closed Principle (OCP):** Software entities must be open for extension but closed for modification.
  Use polymorphism instead of excessive conditional checks (`if-else`/`when`).
- **Composition over Inheritance:** Functionality should preferably be extended by composing objects (composition) rather than using deep inheritance hierarchies (inheritance).
- **Modularization:** Subdivide large systems into loosely coupled, coherent modules or packages that can be developed, tested, and replaced independently.
- **Avoid Leaky Abstractions:** Ensure that modules properly encapsulate their internal implementation details. Other components should only know the public interface and must not rely on or be aware of the underlying mechanics (e.g., specific scripts, file paths, or internal data structures).

### 3. Testability & Pragmatism

- **Testable Architecture:** Choose structures so that business logic can be tested without dependency on frameworks (e.g., UI context or real databases).
- **Dependency Injection (DI):** Inject dependencies via constructors to enable easy replacement with mocks or fakes in tests.
- **KISS Principle (Keep It Simple, Stupid):** Prefer the simplest architecture that reliably and scalably solves the problem.
  Avoid overengineering.

## Code Generation

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
