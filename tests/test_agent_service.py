import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from langchain_core.documents import Document

from agent_service import AgentService
from tools.rag_tool import RAGTool


class FakeRagService:
    def __init__(self):
        self.queries = []

    def retrieve_documents(self, question):
        self.queries.append(question)
        return [
            Document(
                page_content="资料片段",
                metadata={"source": "demo.pdf", "page": 3},
            )
        ]

    def format_documents(self, docs):
        return "\n".join(doc.page_content for doc in docs)

    def format_sources(self, docs):
        return [{"source": "demo.pdf", "page": 3}]


class FakeChatModel:
    def __init__(self, relevance="Action: use_context", chunks=None):
        self.relevance = relevance
        self.chunks = chunks or ["回答"]

    def invoke(self, _messages):
        return type("Message", (), {"content": self.relevance})()

    def stream(self, _messages):
        for chunk in self.chunks:
            yield type("Chunk", (), {"content": chunk})()


class FakeWeatherTool:
    def __init__(self):
        self.locations = []

    def run(self, location=""):
        self.locations.append(location)
        return type("WeatherResult", (), {
            "ok": True,
            "summary": "杭州当前天气：晴，温度 28℃。",
        })()


class AgentServiceTests(unittest.TestCase):
    def test_auto_mode_always_searches_then_uses_relevant_context(self):
        rag_service = FakeRagService()
        agent = AgentService(
            rag_tool=RAGTool(rag_service),
            chat_model=FakeChatModel("Thought: 资料有用\nAction: use_context"),
        )

        events = list(agent.stream_answer("总结资料", "s1", rag_mode="auto"))

        self.assertEqual(rag_service.queries, ["总结资料"])
        self.assertEqual(len(rag_service.queries), 1)
        self.assertIn({"type": "sources", "sources": [{"source": "demo.pdf", "page": 3}]}, events)
        self.assertEqual(events[-1], {"type": "done"})

    def test_auto_mode_searches_but_hides_irrelevant_sources(self):
        rag_service = FakeRagService()
        agent = AgentService(
            rag_tool=RAGTool(rag_service),
            chat_model=FakeChatModel("Thought: 资料无关\nAction: ignore_context"),
        )

        events = list(agent.stream_answer("你好", "s1", rag_mode="auto"))

        self.assertEqual(rag_service.queries, ["你好"])
        self.assertEqual(len(rag_service.queries), 1)
        self.assertFalse(any(event["type"] == "sources" for event in events))
        self.assertEqual(events[-1], {"type": "done"})

    def test_force_mode_calls_rag_without_agent_decision(self):
        rag_service = FakeRagService()
        agent = AgentService(
            rag_tool=RAGTool(rag_service),
            chat_model=FakeChatModel("Action: ignore_context"),
        )

        list(agent.stream_answer("总结资料", "s1", rag_mode="force"))

        self.assertEqual(rag_service.queries, ["总结资料"])

    def test_off_mode_disables_rag_tool(self):
        rag_service = FakeRagService()
        agent = AgentService(
            rag_tool=RAGTool(rag_service),
            chat_model=FakeChatModel("Action: use_context"),
        )

        list(agent.stream_answer("总结资料", "s1", rag_mode="off"))

        self.assertEqual(rag_service.queries, [])

    def test_weather_tool_runs_when_agent_selects_it(self):
        rag_service = FakeRagService()
        weather_tool = FakeWeatherTool()
        agent = AgentService(
            rag_tool=RAGTool(rag_service),
            weather_tool=weather_tool,
            chat_model=FakeChatModel("Action: use_weather\nLocation: 杭州"),
        )

        with patch("agent_service.get_settings", return_value={"agent_tools": {"weather": True}}):
            events = list(agent.stream_answer("杭州天气怎么样", "s1", rag_mode="off"))

        self.assertEqual(weather_tool.locations, ["杭州"])
        self.assertTrue(any(event.get("type") == "tool" and event.get("name") == "weather" for event in events))


if __name__ == "__main__":
    unittest.main()
