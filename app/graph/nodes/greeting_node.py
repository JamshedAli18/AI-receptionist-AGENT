from app.graph.state import ReceptionistState


def greeting_node(state: ReceptionistState) -> dict:
    """First node on a fresh call — only runs when there's no transcript yet."""
    greeting = "Thanks for calling BrightPath Clinic. How can I help you today?"
    return {
        "response_text": greeting,
        "transcript": state.get("transcript", []) + [{"role": "assistant", "content": greeting}],
    }