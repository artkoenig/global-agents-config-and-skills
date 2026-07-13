---
name: architecture-principles
description: MANDATORY FOR DESIGN. This skill MUST be read and applied BEFORE making architectural decisions, choosing libraries/patterns, defining component boundaries, or doing cross-module refactoring.
user-invocable: false
---

# Architecture Principles

For architectural decisions or cross-module refactoring, follow these principles:

## 1. State Management

- **Unidirectional Data Flow (UDF):** Data moves strictly in one direction (e.g., state flows down to the UI, events flow up to logic) to keep the system state deterministic.
- **Single Source of Truth (SSOT):** Every state exists in only a single, clearly defined place.
  Avoid redundant or synchronized states.
- **Immutability:** Data structures and states should be defined as immutable by default.
  Changes produce new instances instead of mutating existing objects.

## 2. Extensibility & Modularity

- **Open/Closed Principle (OCP):** Software entities must be open for extension but closed for modification.
  Use polymorphism instead of excessive conditional checks (`if-else`/`when`).
- **Composition over Inheritance:** Functionality should preferably be extended by composing objects (composition) rather than using deep inheritance hierarchies (inheritance).
- **Modularization:** Subdivide large systems into loosely coupled, coherent modules or packages that can be developed, tested, and replaced independently.
- **Avoid Leaky Abstractions:** Ensure that modules properly encapsulate their internal implementation details. Other components should only know the public interface and must not rely on or be aware of the underlying mechanics (e.g., specific scripts, file paths, or internal data structures).

## 3. Testability & Pragmatism

- **Testable Architecture:** Choose structures so that business logic can be tested without dependency on frameworks (e.g., UI context or real databases).
- **Dependency Injection (DI):** Inject dependencies via constructors to enable easy replacement with mocks or fakes in tests.
- **KISS Principle (Keep It Simple, Stupid):** Prefer the simplest architecture that reliably and scalably solves the problem.
  Avoid overengineering.
