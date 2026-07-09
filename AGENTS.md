- Never use the em dash "—".
  Use plain dash "-" instead.
- When writing commit messages, NEVER auto-add your agent name as co-author.
- Never manually modify CHANGELOG.md files or any files that are marked as auto-generated.
- When writing or substantially editing long Markdown files, put each full sentence on its own line.
  Preserve normal Markdown structure, but avoid wrapping multiple sentences onto one physical line.
- When making technical decisions, do not give much weight to development cost.
  Instead, prefer quality, simplicity, robustness, scalability, and long term maintainability.
- When doing bug fixes, always start with reproducing the bug in an E2E setting as closely aligned with how an end user experiences it.
  This makes sure you find the real problem so your fix will actually solve it.
- When end-to-end testing a product, be picky about the UI you see and be obsessed with pixel perfection.
  If something clearly looks off, even if it is not directly related to what you are doing, try to get it fixed along the way.
- Apply that same high standard to engineering excellence: lint, test failures, and test flakiness.
  If you see one, even if it is not caused by what you are working on right now, still get it fixed.

### Architectural Decisions & Cross-Module Refactoring

For architectural decisions or cross-module refactoring, follow these principles:

#### 1. State Management

- **Unidirectional Data Flow (UDF):** Data moves strictly in one direction (e.g., state flows down to the UI, events flow up to logic) to keep the system state deterministic.
- **Single Source of Truth (SSOT):** Every state exists in only a single, clearly defined place.
  Avoid redundant or synchronized states.
- **Immutability:** Data structures and states should be defined as immutable by default.
  Changes produce new instances instead of mutating existing objects.

#### 2. Extensibility & Modularity

- **Open/Closed Principle (OCP):** Software entities must be open for extension but closed for modification.
  Use polymorphism instead of excessive conditional checks (`if-else`/`when`).
- **Composition over Inheritance:** Functionality should preferably be extended by composing objects (composition) rather than using deep inheritance hierarchies (inheritance).
- **Modularization:** Subdivide large systems into loosely coupled, coherent modules or packages that can be developed, tested, and replaced independently.
- **Avoid Leaky Abstractions:** Ensure that modules properly encapsulate their internal implementation details. Other components should only know the public interface and must not rely on or be aware of the underlying mechanics (e.g., specific scripts, file paths, or internal data structures).

#### 3. Testability & Pragmatism

- **Testable Architecture:** Choose structures so that business logic can be tested without dependency on frameworks (e.g., UI context or real databases).
- **Dependency Injection (DI):** Inject dependencies via constructors to enable easy replacement with mocks or fakes in tests.
- **KISS Principle (Keep It Simple, Stupid):** Prefer the simplest architecture that reliably and scalably solves the problem.
  Avoid overengineering.

### Code Generation Principles

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
