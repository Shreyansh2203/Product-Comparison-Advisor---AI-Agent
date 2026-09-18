# Product Comparison Advisor (AI Agent)

This repository contains the declarative workflow configuration for an enterprise AI agent that automates product comparisons within Oracle Fusion. 

Developed and deployed for **Verdesian Life Sciences**, the agent integrates directly with Oracle Supply Chain Management (SCM) REST APIs to extract item attributes and generate dynamic comparison reports.

## Architecture & Tech Stack

*   **Model:** OCI GPT-5 Mini (Oracle Cloud Infrastructure)
*   **Integration:** Oracle Fusion SCM REST APIs
*   **Endpoints Used:** `itemOperationalAttributes`, `itemExtendedAttributes`, `itemsV2`
*   **Format:** Single-Agent Declarative Workflow (JSON)

## Core Capabilities

*   **API Orchestration:** Executes sequential API calls to extract internal `ItemId` and `OrganizationId`, followed by deep dives into extended attributes and product costs.
*   **Data Transformation:** Translates internal database lookup codes (e.g., boolean flags, Lot Control Codes) into human-readable business terms before presenting data.
*   **Hallucination Guardrails:** Enforces strict prompt constraints, ensuring the model only evaluates whitelisted attributes and prevents interpolation of missing data.
*   **Dynamic UI Generation:** Instructs the LLM to output custom HTML tables, applying specific inline CSS to highlight data discrepancies across compared items.
*   **Context Optimization:** Discards raw JSON payloads immediately after extracting necessary fields to minimize token usage and prevent context window bloat.

## Deployment Lifecycle

This configuration was tested and deployed following a standard enterprise Software Development Life Cycle (SDLC):

*   **DEV1 & DEV2:** Agent prompt tuning, API integration testing, and HTML rendering validation.
*   **TEST:** Quality assurance and User Acceptance Testing (UAT) using real-world enterprise product data.

## Repository Contents

*   `PRODUCT_COMPARATOR_V13.json`: The core JSON export containing the agent's system prompts, REST tool definitions, API endpoints, and error handling logic.
