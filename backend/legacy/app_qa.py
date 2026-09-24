"""KnowFlow 个人知识库应用主页。"""

from pathlib import Path

import streamlit as st

import config_data as cfg
from app_file_uploader import render_file_uploader
from file_history_store import get_history
from rag import RagService
from ui_components import (
    apply_page_style,
    render_brand,
    render_hero,
    render_note,
    render_section_title,
)


BASE_DIR = Path(__file__).resolve().parent
USER_AVATAR = str(BASE_DIR / "assets" / "user_avatar.svg")
ASSISTANT_AVATAR = str(BASE_DIR / "assets" / "assistant_avatar.svg")
WELCOME_MESSAGE = "你好，我会优先根据你上传的资料回答问题。现在想了解什么？"


st.set_page_config(
    page_title="KnowFlow · 个人知识库",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_page_style()


with st.sidebar:
    render_brand()
    current_page = st.radio(
        "功能导航",
        ["智能问答", "知识库管理", "使用说明"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    session_id = st.text_input(
        "会话名称",
        value=st.session_state.get("session_id", "user001"),
        help="不同名称会使用独立的对话历史。",
    ).strip() or "user001"

    if st.session_state.get("session_id") != session_id:
        st.session_state.session_id = session_id
        st.session_state.messages = [
            {"role": "assistant", "content": WELCOME_MESSAGE}
        ]

    if st.button("新建对话", use_container_width=True):
        get_history(session_id).clear()
        st.session_state.messages = [
            {"role": "assistant", "content": WELCOME_MESSAGE}
        ]
        st.rerun()

    st.caption("本地持久化 · Chroma 向量检索")


if current_page == "智能问答":
    render_hero(
        "RAG assistant",
        "从你的资料中获得可信回答",
        "输入问题，KnowFlow 会检索个人知识库，结合会话上下文生成简洁、专业的回答。",
    )

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": WELCOME_MESSAGE}
        ]
    if "rag" not in st.session_state:
        st.session_state.rag = RagService()

    if len(st.session_state.messages) == 1:
        render_section_title("spark", "你可以这样问")
        suggestion_columns = st.columns(3)
        suggestions = [
            "概括我的知识库主要内容",
            "列出资料中的核心观点",
            "根据资料给我一份学习计划",
        ]
        selected_suggestion = None
        for index, suggestion in enumerate(suggestions):
            if suggestion_columns[index].button(
                suggestion,
                use_container_width=True,
                key=f"suggestion_{index}",
            ):
                selected_suggestion = suggestion
    else:
        selected_suggestion = None

    render_section_title("chat", "对话")
    for message in st.session_state.messages:
        avatar = USER_AVATAR if message["role"] == "user" else ASSISTANT_AVATAR
        st.chat_message(message["role"], avatar=avatar).write(message["content"])

    typed_prompt = st.chat_input("向你的知识库提问...")
    prompt = typed_prompt or selected_suggestion

    if prompt:
        st.chat_message("user", avatar=USER_AVATAR).write(prompt)
        st.session_state.messages.append(
            {"role": "user", "content": prompt}
        )

        session_config = {
            "configurable": {
                "session_id": session_id,
            }
        }
        with st.spinner("正在检索知识库..."):
            with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
                result_stream = st.session_state.rag.chain.stream(
                    {"input": prompt},
                    config=session_config,
                )
                result = st.write_stream(result_stream)

        st.session_state.messages.append(
            {"role": "assistant", "content": result}
        )

elif current_page == "知识库管理":
    render_file_uploader(show_title=True)

else:
    render_hero(
        "Quick start",
        "三步建立你的个人知识库",
        "从上传资料到连续对话，整个流程都在本应用中完成。",
    )
    guide_columns = st.columns(3, gap="large")
    with guide_columns[0]:
        render_note("file", "1. 上传资料", "打开知识库管理，选择 PDF 或 UTF-8 TXT 文件。")
    with guide_columns[1]:
        render_note("database", "2. 生成索引", "确认文件后点击解析，系统会自动切分并写入向量库。")
    with guide_columns[2]:
        render_note("chat", "3. 开始问答", "返回智能问答，用自然语言检索和理解你的资料。")

    render_section_title("shield", "数据与会话")
    render_note("shield", "本地知识库", "文档向量和会话记录保存在当前项目目录中。")
    render_note("chat", "独立会话", "修改侧边栏中的会话名称，可以切换不同的对话历史。")
