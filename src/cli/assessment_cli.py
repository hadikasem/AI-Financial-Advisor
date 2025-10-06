"""
Command-line interface for risk assessment.

This module provides the CLI for running risk assessments interactively.
"""

from ..core.assessment import RiskAssessmentAgent
from ..services.llm import call_llm, LiveLLMGoalsProvider


def main():
    """Main CLI entry point for risk assessment."""
    agent = RiskAssessmentAgent(
        llm_fn=call_llm, 
        goals_provider=LiveLLMGoalsProvider(llm_fn=call_llm)
    )
    
    print("Type 'restart' or 'retry' anytime. Ask finance questions anytime (e.g., 'What is an ETF?').\n")
    print(agent.start())
    
    while True:
        try:
            user = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break
        
        out = agent.receive_user_message(user)
        print(out)
        
        if agent.step.value == "complete":
            break


if __name__ == "__main__":
    main()
