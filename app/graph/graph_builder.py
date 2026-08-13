from langgraph.graph import StateGraph, END
from langgraph.checkpoint.mongodb import MongoDBSaver

from app.config import MONGODB_URI
from app.graph.state import ReceptionistState
from app.graph.nodes.greeting_node import greeting_node
from app.graph.nodes.intent_node import intent_node
from app.graph.nodes.faq_node import faq_node
from app.graph.nodes.escalation_node import escalation_node
from app.graph.nodes.small_talk_node import small_talk_node
from app.graph.nodes.booking_node import booking_node
from app.graph.nodes.reschedule_cancel_node import reschedule_cancel_node
from app.graph.nodes.end_call_node import end_call_node
from app.graph.edges import route_after_intent, route_after_faq

# Held at module level, deliberately never exited — this keeps the
# underlying MongoClient connection alive for the entire process lifetime.
# If this were a local variable inside build_graph(), Python would garbage
# collect it once the function returns, silently closing the connection
# on the very next graph invocation.
_checkpointer_cm = MongoDBSaver.from_conn_string(MONGODB_URI)
_checkpointer = _checkpointer_cm.__enter__()


def build_graph():
    graph = StateGraph(ReceptionistState)

    graph.add_node("greeting_node", greeting_node)
    graph.add_node("intent_node", intent_node)
    graph.add_node("faq_node", faq_node)
    graph.add_node("escalation_node", escalation_node)
    graph.add_node("small_talk_node", small_talk_node)
    graph.add_node("booking_node", booking_node)
    graph.add_node("reschedule_cancel_node", reschedule_cancel_node)
    graph.add_node("end_call_node", end_call_node)

    graph.set_entry_point("intent_node")

    graph.add_conditional_edges(
        "intent_node",
        route_after_intent,
        {
            "faq_node": "faq_node",
            "escalation_node": "escalation_node",
            "small_talk_node": "small_talk_node",
            "booking_node": "booking_node",
            "reschedule_cancel_node": "reschedule_cancel_node",
        },
    )

    graph.add_conditional_edges(
        "faq_node",
        route_after_faq,
        {"escalation_node": "escalation_node", "end": END},
    )

    graph.add_edge("escalation_node", END)
    graph.add_edge("small_talk_node", END)
    graph.add_edge("booking_node", END)
    graph.add_edge("reschedule_cancel_node", END)
    graph.add_edge("end_call_node", END)

    return graph.compile(checkpointer=_checkpointer)


receptionist_graph = build_graph()