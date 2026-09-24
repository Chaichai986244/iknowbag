import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from file_history_store import get_history
from rag import RagService
from tools.rag_tool import RAGTool
from settings_store import get_settings
from tools.weather_tool import WeatherTool


load_dotenv()


class AgentService:
    def __init__(self, rag_tool=None, chat_model=None, weather_tool=None):
        self.rag_tool = rag_tool or RAGTool(RagService())
        self.weather_tool = weather_tool or WeatherTool()
        self.chat_model = chat_model or ChatOpenAI(
            api_key=os.getenv("STEPFUN_API_KEY"),
            base_url=os.getenv("STEPFUN_BASE_URL"),
            model="step-3.7-flash",
        )

    def decide_weather_tool(self, question: str):
        messages = [
            SystemMessage(content=(
                "你是一个 ReAct Agent 的工具选择器。判断用户问题是否需要查询实时天气。"
                "需要天气工具的场景包括但不限于：直接询问天气/温度/下雨/风力/湿度；"
                "询问今天/明天适合做什么户外活动（出去玩、跑步、爬山、郊游、钓鱼等）；"
                "询问需要带伞、穿什么衣服、冷不冷、热不热、会不会下雨等生活建议。"
                "如果需要，尽量提取用户指定的位置；如果用户没说位置，Location 留空。"
                "只能输出两行：Action: use_weather 或 skip_weather；Location: 位置"
            )),
            HumanMessage(content=question),
        ]
        response = self.chat_model.invoke(messages)
        content = str(response.content)
        lower = content.lower()
        if "use_weather" not in lower:
            return False, ""
        location = ""
        for line in content.splitlines():
            if line.lower().startswith("location:") or line.startswith("Location："):
                location = line.split(":", 1)[-1].strip() if ":" in line else line.split("：", 1)[-1].strip()
        return True, location

    def grade_context(self, question: str, context: str) -> str:
        messages = [
            SystemMessage(content=(
                "你是一个 ReAct Agent。RAG 工具已经返回了 Observation。"
                "请判断这些资料片段是否能帮助回答用户问题。"
                "如果资料与问题相关且可作为依据，选择 use_context。"
                "如果资料无关、太弱、答非所问或没有有效信息，选择 ignore_context。"
                "只能输出两行：Thought: 简短理由；Action: use_context 或 ignore_context。"
            )),
            HumanMessage(content=f"用户问题：{question}\n\nObservation:\n{context}"),
        ]
        response = self.chat_model.invoke(messages)
        content = str(response.content).lower()
        if "action: use_context" in content or "action：use_context" in content:
            return "use_context"
        return "ignore_context"

    def build_answer_messages(self, question: str, context: str, session_id: str):
        history = get_history(session_id)
        messages = [
            SystemMessage(content=(
                "你是一个个人知识库 Agent。根据可用 Observation 回答用户。"
                "Observation 可能包含知识库资料、天气工具结果，或没有工具结果。"
                "如果 Observation 中有工具结果，应该自然参考它；如果没有资料，就直接回答。"
                f"\n\nObservation:\n{context}"
            )),
            *history.messages,
            HumanMessage(content=question),
        ]
        return messages

    def stream_model_answer(self, question: str, context: str, session_id: str):
        full_text = ""
        for chunk in self.chat_model.stream(
            self.build_answer_messages(question, context, session_id)
        ):
            content = str(getattr(chunk, "content", chunk))
            full_text += content
            yield {"type": "chunk", "content": content}

        history = get_history(session_id)
        history.add_user_message(question)
        history.add_ai_message(full_text)

    def stream_answer(self, question, session_id, stop_event=None, rag_mode="auto", client_ip=""):
        observations = []
        context = "没有调用工具。"
        use_context = False
        settings = get_settings()

        if settings["agent_tools"]["weather"]:
            yield {"type": "status", "content": "正在判断是否需要天气工具"}
            should_use_weather, weather_location = self.decide_weather_tool(question)
            if should_use_weather:
                yield {"type": "status", "content": "正在查询实时天气"}
                weather_result = self.weather_tool.run(weather_location, client_ip=client_ip)
                observations.append(f"Weather Observation:\n{weather_result.summary}")
                yield {
                    "type": "tool",
                    "name": "weather",
                    "content": weather_result.summary,
                    "ok": weather_result.ok,
                }
        else:
            yield {"type": "status", "content": "Agent 天气工具未启用"}

        if rag_mode == "force":
            yield {"type": "status", "content": "强制参考：正在检索知识库"}
            tool_result = self.rag_tool.run(question)
            observations.append(f"RAG Observation:\n{tool_result.context}")
            context = "\n\n".join(observations)
            use_context = True
            yield {"type": "sources", "sources": tool_result.sources}
        elif rag_mode == "auto":
            yield {"type": "status", "content": "智能筛选：正在检索知识库"}
            tool_result = self.rag_tool.run(question)
            yield {"type": "status", "content": "正在判断检索结果是否有用"}
            use_context = self.grade_context(question, tool_result.context) == "use_context"
            if use_context:
                observations.append(f"RAG Observation:\n{tool_result.context}")
                context = "\n\n".join(observations)
                yield {"type": "sources", "sources": tool_result.sources}
                yield {"type": "status", "content": "资料可用，正在参考回答"}
            else:
                context = "\n\n".join(observations) if observations else context
                yield {"type": "status", "content": "资料不匹配，正在直接回答"}
        else:
            context = "\n\n".join(observations) if observations else context
            yield {"type": "status", "content": "已关闭 RAG 工具，Agent 将直接回答"}

        if observations and context == "没有调用工具。":
            context = "\n\n".join(observations)

        for event in self.stream_model_answer(question, context, session_id):
            if stop_event is not None and stop_event.is_set():
                return
            yield event
        yield {"type": "done"}
