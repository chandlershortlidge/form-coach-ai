import os
import sys

import pytest


@pytest.fixture
def graph_module(tmp_path, monkeypatch):
    """Import app.graph with a tmp Chroma dir so it doesn't litter the cwd."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("CHROMA_DIR", str(tmp_path / "chroma"))
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)

    sys.modules.pop("app.graph", None)
    from app import graph
    return graph


def test_route_query_with_video_goes_to_encoder(graph_module):
    state = {"user_video": "/tmp/clip.mp4", "user_query": "ignored"}

    assert graph_module.route_query(state) == "video_encoder"


class _FakeChain:
    def __init__(self, response):
        self.response = response

    def invoke(self, payload):
        return self.response


def test_route_query_to_vector_db_when_classifier_says_vectorstore(graph_module, monkeypatch):
    monkeypatch.setattr(graph_module, "router_chain", _FakeChain("vectorstore & memory"))

    state = {"user_video": "", "user_query": "is this good squat technique?"}

    assert graph_module.route_query(state) == "vector_db"


def test_route_query_to_chat_memory_when_classifier_says_memory(graph_module, monkeypatch):
    monkeypatch.setattr(graph_module, "router_chain", _FakeChain("memory"))

    state = {"user_video": "", "user_query": "thanks for your help!"}

    assert graph_module.route_query(state) == "chat_memory"


def test_route_query_classifier_output_is_case_insensitive(graph_module, monkeypatch):
    monkeypatch.setattr(graph_module, "router_chain", _FakeChain("  VECTORSTORE & MEMORY  "))

    state = {"user_video": "", "user_query": "how should I grip the bar?"}

    assert graph_module.route_query(state) == "vector_db"
