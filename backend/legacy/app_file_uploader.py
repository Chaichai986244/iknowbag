"""知识库文件上传页面。"""

import base64
import html

import streamlit as st
import streamlit.components.v1 as components

import config_data as cfg
from knowledge_base import KnowledgeBaseService
from ui_components import (
    apply_page_style,
    render_hero,
    render_note,
    render_section_title,
    render_stats,
)


def get_knowledge_base_service():
    if "knowledge_base_service" not in st.session_state:
        st.session_state.knowledge_base_service = KnowledgeBaseService()
    return st.session_state.knowledge_base_service


def render_file_uploader(show_title: bool = True):
    """渲染 PDF/TXT 上传、预览和向量库写入功能。"""
    if show_title:
        render_hero(
            "Knowledge workspace",
            "搭建你的个人知识库",
            "上传 PDF 或 TXT 资料，系统会自动提取文本、切分内容并生成向量索引。",
        )

    service = get_knowledge_base_service()

    try:
        statistics = service.get_statistics()
        render_stats(
            document_count=statistics["document_count"],
            source_count=statistics["source_count"],
            collection_name=cfg.collection_name,
        )
    except Exception as error:
        statistics = {"sources": []}
        st.warning(f"暂时无法读取知识库统计：{error}")

    left_column, right_column = st.columns([1.6, 1], gap="large")

    with left_column:
        render_section_title("file", "上传新资料")
        uploader_file = st.file_uploader(
            "选择 PDF 或 TXT 文件",
            type=["pdf", "txt"],
            accept_multiple_files=False,
            key="knowledge_base_file_uploader",
        )

    with right_column:
        render_section_title("shield", "处理说明")
        render_note("file", "自动切分", "文档会按自然段落切分，并保留文件名和 PDF 页码。")
        render_note("database", "重复检测", "使用文件指纹防止相同资料被重复写入。")

    if uploader_file is not None:
        file_name = uploader_file.name
        file_type = uploader_file.type
        file_size = uploader_file.size / 1024 / 1024
        file_bytes = uploader_file.getvalue()
        is_pdf = file_name.lower().endswith(".pdf")

        st.markdown("---")
        render_section_title("file", "文件确认")
        info_columns = st.columns(3)
        info_columns[0].metric("文件名", file_name)
        info_columns[1].metric("格式", "PDF" if is_pdf else "TXT")
        info_columns[2].metric("大小", f"{file_size:.2f} MB")

        text = None
        if is_pdf:
            with st.expander("预览 PDF", expanded=False):
                pdf_base64 = base64.b64encode(file_bytes).decode()
                pdf_html = (
                    f'<iframe src="data:application/pdf;base64,{pdf_base64}" '
                    'width="100%" height="600px" type="application/pdf"></iframe>'
                )
                components.html(pdf_html, height=620)
        else:
            try:
                text = file_bytes.decode("utf-8-sig")
                with st.expander("预览 TXT", expanded=False):
                    st.text(text[:2000])
            except UnicodeDecodeError:
                st.error("TXT 文件不是 UTF-8 编码，请转换编码后重试。")

        upload_disabled = not is_pdf and text is None
        if st.button(
            "解析并存入知识库",
            type="primary",
            disabled=upload_disabled,
            use_container_width=True,
            key="save_file_to_vector_store",
        ):
            with st.spinner("正在解析、切分并写入向量库..."):
                try:
                    if is_pdf:
                        result = service.upload_pdf(
                            pdf_bytes=file_bytes,
                            file_name=file_name,
                        )
                    else:
                        result = service.upload_by_str(
                            data=text,
                            file_name=file_name,
                        )

                    if "成功" in result:
                        st.success(result)
                    else:
                        st.warning(result)
                except Exception as error:
                    st.error(f"上传失败：{error}")

    sources = statistics.get("sources") or []
    if sources:
        st.markdown("---")
        render_section_title("database", "已收录的资料")
        source_html = "".join(
            f'<span class="app-source">{html.escape(source)}</span>'
            for source in sources
        )
        st.markdown(source_html, unsafe_allow_html=True)


if __name__ == "__main__":
    st.set_page_config(
        page_title="KnowFlow · 知识库",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    apply_page_style()
    render_file_uploader(show_title=True)
