from app.graph.state import ReceptionistState

CLOSING_MESSAGE = "Thanks for calling BrightPath Clinic. Take care!"


def end_call_node(state: ReceptionistState) -> dict:
    return {
        "response_text": CLOSING_MESSAGE,
        "call_ended": True,
        "transcript": state.get("transcript", []) + [{"role": "assistant", "content": CLOSING_MESSAGE}],
    }