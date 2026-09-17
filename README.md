# Product Comparison Advisor - AI Agent

An intelligent, autonomous AI Agent designed to help Product Designers, Product Managers, and Quality Engineers seamlessly compare Oracle Fusion products and items. 

Developed and rigorously tested for enterprise deployment at **Verdesian Life Sciences**, this repository contains the declarative configuration and workflow definitions for an AI agent that integrates directly with Oracle Supply Chain Management (SCM) systems to generate dynamic, visually highlighted product comparisons.

## 🚀 Key Features

*   **Intelligent Data Retrieval:** Autonomously orchestrates calls to Oracle SCM REST APIs to fetch operational attributes, extended attributes, and product costs.
*   **Data Transformation:** Automatically translates internal database lookup codes (e.g., Boolean flags, Lot Control Codes) into human-readable business terms.
*   **Dynamic UI Generation:** The agent's prompt engineering directs the LLM to output custom, styled HTML tables that dynamically highlight attribute differences across multiple items for a premium frontend experience.
*   **Hallucination Prevention:** Strict prompt guardrails ensure the agent only outputs whitelisted attributes and never invents missing data.
*   **Context Optimization:** Designed to extract and retain only vital identifiers (Item ID, Organization ID) to minimize token usage and context window bloat.

## 🛠️ Technology Stack

*   **AI Model:** OCI GPT-5 Mini (Oracle Cloud Infrastructure)
*   **Integrations:** Oracle Fusion SCM REST APIs
    *   `itemOperationalAttributes`
    *   `itemExtendedAttributes`
    *   `itemsV2` (Product Costs)
*   **Architecture:** Single-Agent Workflow (Declarative JSON)

## 🏢 Enterprise SDLC & Deployment

This architecture follows a rigorous Software Development Life Cycle (SDLC) and has been successfully validated across multiple environments for **Verdesian Life Sciences**:

*   **DEV1 & DEV2 Instances:** Initial agent prompt tuning, REST API integration testing, and HTML UI rendering validation.
*   **TEST Instance:** Quality assurance and User Acceptance Testing (UAT) with real-world enterprise product data to ensure absolute accuracy and strict adherence to anti-hallucination guardrails.

## 🧠 How It Works

1.  **Trigger:** The agent receives an item comparison request via a REST trigger.
2.  **Sequential Execution:** It first queries the operational attributes to extract the internal `ItemId` and `OrganizationId`.
3.  **Deep Dive:** Using the extracted IDs, it makes subsequent calls to retrieve extended attributes and cost parameters.
4.  **Analysis & Formatting:** The LLM processes the payloads, comparing exact strings across items.
5.  **Output:** It generates a robust HTML block featuring:
    *   A summary of the comparison.
    *   A meticulously styled table grouping attributes by category (Overview, Product Details, Manufacturing, etc.).
    *   Highlighted rows where discrepancies exist between items.
    *   Cross-module insights and business summaries.

## 📁 Repository Structure

*   `PRODUCT_COMPARATOR_V13.json`: The core export of the AI agent's workflow, containing the system prompts, tool definitions, API endpoints, and error handling configurations.
