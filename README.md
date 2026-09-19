# Oracle Fusion Product Comparison Advisor

## Executive Summary
This repository contains the configuration and operational workflow for an enterprise-grade AI agent developed for **Verdesian Life Sciences**. The Product Comparison Advisor automates the extraction, transformation, and comparison of product data within Oracle Fusion, significantly accelerating workflows for Product Managers, Designers, and Quality Engineers.

## Business Value
*   **Automated Intelligence:** Eliminates manual data aggregation by directly querying Oracle Supply Chain Management (SCM) environments.
*   **Standardized Reporting:** Generates deterministic, dynamically highlighted HTML reports for immediate visual identification of product discrepancies.
*   **Data Integrity:** Employs strict prompt guardrails to prevent data interpolation (hallucinations), ensuring business decisions are made on exact source-of-truth data.

## Technical Architecture
*   **Inference Engine:** OCI GPT-5 Mini (Oracle Cloud Infrastructure)
*   **Integration Layer:** Oracle Fusion SCM REST APIs
    *   `itemOperationalAttributes`
    *   `itemExtendedAttributes`
    *   `itemsV2` (Product Costs)
*   **Workflow Format:** Single-Agent Declarative JSON

## Core System Capabilities
*   **API Orchestration:** Executes a sequenced data retrieval pipeline. It identifies the internal `ItemId` and `OrganizationId`, then triggers targeted queries for extended attributes and cost structures.
*   **Data Normalization:** Translates internal database lookup codes (e.g., boolean flags, Lot Control Codes) into human-readable business taxonomy prior to data presentation.
*   **Hallucination Prevention:** The agent is constrained by strict evaluation parameters. It is restricted to whitelisted attributes and explicitly programmed to fail gracefully rather than invent missing data.
*   **Dynamic UI Generation:** Outputs structured HTML with embedded CSS, applying conditional formatting to highlight variations across compared products.
*   **Context Optimization:** Implements aggressive context window management by discarding raw JSON payloads immediately after field extraction, optimizing token utilization and reducing latency.

## Software Development Life Cycle (SDLC)
The architecture adheres to a structured, multi-environment deployment strategy:
*   **DEV1 & DEV2 Instances:** System integration testing (SIT), prompt tuning, and HTML rendering validation.
*   **TEST Instance:** User Acceptance Testing (UAT) utilizing real-world enterprise product data to validate accuracy against strict quality assurance metrics.

## Repository Contents
*   `PRODUCT_COMPARATOR_V13.json`: The production-ready configuration file containing the agent's behavioral prompts, REST endpoint definitions, and error handling protocols.
