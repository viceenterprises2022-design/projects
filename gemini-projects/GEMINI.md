# GEMINI.MD: AI Collaboration Guide

This document provides essential context for AI models interacting with this project. Adhering to these guidelines will ensure consistency and maintain code quality.

## 1. Project Overview & Purpose

* **Primary Goal:** (Inferred) This project appears to be a placeholder or a new repository for Gemini-related projects. As it is currently empty, its specific goal is yet to be defined. (Confidence: Low)
* **Business Domain:** (Inferred) General software development and AI integration experiments. (Confidence: Low)

## 2. Core Technologies & Stack

* **Languages:** (Inferred) JavaScript/TypeScript, based on the presence of `package-lock.json`. (Confidence: Medium)
* **Frameworks & Runtimes:** (Inferred) Node.js, as indicated by the npm lockfile. (Confidence: High)
* **Databases:** (Inferred) Not yet determined. (Confidence: N/A)
* **Key Libraries/Dependencies:** (Inferred) None yet installed. (Confidence: N/A)
* **Package Manager(s):** `npm` (Confidence: High)

## 3. Architectural Patterns

* **Overall Architecture:** (Inferred) Likely to follow a modular structure as the project grows. (Confidence: Low)
* **Directory Structure Philosophy:** (Suggested)
    * `/src`: For all primary source code.
    * `/docs`: For documentation and architectural designs.
    * `/tests`: For unit and integration tests.

## 4. Coding Conventions & Style Guide

* **Formatting:** (Inferred) Standard JavaScript/TypeScript conventions (e.g., 2-space indentation). Recommended: Prettier and ESLint. (Confidence: Medium)
* **Naming Conventions:** (Inferred)
    * `variables`, `functions`: camelCase (`myVariable`)
    * `classes`, `components`: PascalCase (`MyClass`)
    * `files`: kebab-case (`my-component.js`)
* **API Design:** (Inferred) RESTful principles are recommended if an API is developed.
* **Error Handling:** (Inferred) Standard async/await with try...catch blocks for asynchronous operations.

## 5. Key Files & Entrypoints

* **Main Entrypoint(s):** (Inferred) Likely `src/index.js` or `index.ts`. (Confidence: Medium)
* **Configuration:** (Inferred) `.env` for environment variables, `package.json` for project configuration. (Confidence: High)
* **CI/CD Pipeline:** (Inferred) GitHub Actions is recommended if using GitHub.

## 6. Development & Testing Workflow

* **Local Development Environment:** (Inferred) Standard Node.js setup: `npm install` followed by a start script like `npm run dev`. (Confidence: Medium)
* **Testing:** (Inferred) Jest or Vitest are recommended testing frameworks for this stack. (Confidence: Medium)
* **CI/CD Process:** (Inferred) Not yet implemented.

## 7. Specific Instructions for AI Collaboration

* **Contribution Guidelines:** (Inferred) Currently no `CONTRIBUTING.md`. It is recommended to create one to define PR and branching strategies.
* **Infrastructure (IaC):** (Inferred) None detected.
* **Security:** (General) Do not hardcode secrets or keys. Use environment variables for sensitive configuration.
* **Dependencies:** (General) Use `npm install` for production dependencies and `npm install --save-dev` for development tools.
* **Commit Messages:** (Inferred) Conventional Commits (`feat:`, `fix:`, `docs:`) are recommended for clear versioning.
