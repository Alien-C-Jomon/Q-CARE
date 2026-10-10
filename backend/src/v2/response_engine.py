"""
Q-CARE V2 response engine.
"""

def build_response(research, ranking, emergency):
    return {
        "status": "success",
        "version": "V2",
        "research": research,
        "evidence": ranking,
        "emergency": emergency,
        "diagnostic": False,
    }
