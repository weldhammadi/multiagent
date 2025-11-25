"""Compatibility wrapper for older imports.

Re-exports from llm_server_core for backward compatibility.
"""
from llm_server_core import AgentAssembler, AgentType, ExecutionPlan, AgentRequirements

__all__ = ["AgentAssembler", "AgentType", "ExecutionPlan", "AgentRequirements"]
