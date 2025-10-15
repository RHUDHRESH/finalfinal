"""
Orchestrator that defines the agent workflow using LangGraph.
"""

from langgraph.graph import StateGraph, START, END
from karigar.schemas.state import KarigarState
from karigar.agents.intake_agent import IntakeAgent
from karigar.agents.supplier_agent import SupplierAgent
from karigar.agents.commit_agent import CommitAgent
from karigar.agents.sales_agent import SalesAgent
from karigar.agents.cash_agent import CashAgent
import asyncio

class KarigarWorkflow:
    """
    Manages the flow of control between the different agents in the system.
    """
    def __init__(self):
        """Initializes the StateGraph and builds the workflow."""
        self.graph = StateGraph(KarigarState)
        self._build_graph()

    def _build_graph(self):
        """Constructs the graph of agents and their transitions."""
        # Helper function to run async methods within the sync graph
        def run_async_node(node_func):
            def wrapper(state):
                return asyncio.run(node_func(state))
            return wrapper

        # Instantiate agents
        intake_agent = IntakeAgent()
        supplier_agent = SupplierAgent()
        commit_agent = CommitAgent()
        sales_agent = SalesAgent()
        cash_agent = CashAgent()

        # Add nodes to the graph
        self.graph.add_node("intake", intake_agent.process)
        self.graph.add_node("supplier", run_async_node(supplier_agent.process))
        self.graph.add_node("commit", commit_agent.process)
        self.graph.add_node("sales", sales_agent.process)
        self.graph.add_node("cash", cash_agent.process)

        # Define conditional logic
        def should_continue(state: KarigarState) -> str:
            """Determines the next step based on the current state."""
            if state.get("status") == "error":
                return "end"
            
            # After intake, go to supplier search
            if state.get("status") == "intake_complete":
                return "supplier"
            
            # After supplier search, go to commit
            if state.get("status") == "supplier_search_complete":
                return "commit"

            # After commit, go to sales
            if state.get("status") == "commit_complete":
                return "sales"

            # After sales, go to cash ledger
            if state.get("status") in ["sales_complete", "sales_skipped"]:
                return "cash"

            # After cash, end the flow
            if state.get("status") == "cash_complete":
                return "end"
            
            return "end"

        # Add edges to the graph
        self.graph.add_edge(START, "intake")
        self.graph.add_conditional_edges(
            "intake",
            should_continue,
            {"supplier": "supplier", "end": END}
        )
        self.graph.add_conditional_edges(
            "supplier",
            should_continue,
            {"commit": "commit", "end": END}
        )
        self.graph.add_conditional_edges(
            "commit",
            should_continue,
            {"sales": "sales", "end": END}
        )
        self.graph.add_conditional_edges(
            "sales",
            should_continue,
            {"cash": "cash", "end": END}
        )
        self.graph.add_conditional_edges(
            "cash",
            should_continue,
            {"end": END}
        )
        
        # Compile the graph
        self.compiled = self.graph.compile()

    async def run(self, initial_state: dict):
        """
        Runs the agent workflow with a given initial state.
        
        Args:
            initial_state: The starting state for the workflow.
            
        Returns:
            The final state of the workflow after execution.
        """
        return await self.compiled.ainvoke(initial_state)
