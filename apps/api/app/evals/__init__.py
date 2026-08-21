"""Deterministic evaluation suite for the Agent Gateway.

The suite drives the real orchestrator, policy engine, tools, and adapters;
only persistence (fake_db) and the LLM (fake_llm) are faked. See scenarios.py
for the scenario catalog and run_evals.py for report generation.
"""
