"""Streamlit 页面的公共样式和 SVG 组件。"""

import html

import streamlit as st


SVG_ICONS = {
    "brand": """
        <svg viewBox="0 0 48 48" aria-hidden="true">
            <path d="M24 5 39 13.5v17L24 39 9 30.5v-17L24 5Z" fill="none" stroke="currentColor" stroke-width="3"/>
            <path d="M16 20h16M16 27h11" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
            <circle cx="32" cy="27" r="3" fill="currentColor"/>
        </svg>
    """,
    "chat": """
        <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M5 5.5h14v10H9l-4 3v-13Z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>
            <path d="M8 9h8M8 12h5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
        </svg>
    """,
    "database": """
        <svg viewBox="0 0 24 24" aria-hidden="true">
            <ellipse cx="12" cy="5.5" rx="7" ry="3" fill="none" stroke="currentColor" stroke-width="1.8"/>
            <path d="M5 5.5v6c0 1.7 3.1 3 7 3s7-1.3 7-3v-6M5 11.5v6c0 1.7 3.1 3 7 3s7-1.3 7-3v-6" fill="none" stroke="currentColor" stroke-width="1.8"/>
        </svg>
    """,
    "file": """
        <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M7 3.5h7l4 4v13H7v-17Z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>
            <path d="M14 3.5v4h4M10 12h5M10 15.5h5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
        </svg>
    """,
    "shield": """
        <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M12 3.5 19 6v5.5c0 4.1-2.5 7.4-7 9-4.5-1.6-7-4.9-7-9V6l7-2.5Z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>
            <path d="m9 12 2 2 4-4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
    """,
    "spark": """
        <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="m12 3 1.4 4.1L17.5 8.5l-4.1 1.4L12 14l-1.4-4.1-4.1-1.4 4.1-1.4L12 3ZM18.5 14l.8 2.2 2.2.8-2.2.8-.8 2.2-.8-2.2-2.2-.8 2.2-.8.8-2.2Z" fill="currentColor"/>
        </svg>
    """,
}


def icon(name: str) -> str:
    return SVG_ICONS[name]


def apply_page_style():
    st.markdown(
        """
        <style>
        :root {
            --app-primary: #5b6cff;
            --app-primary-soft: rgba(91, 108, 255, 0.12);
            --app-border: rgba(128, 138, 164, 0.22);
            --app-muted: #8b93a7;
        }
        .stApp { background: linear-gradient(145deg, rgba(91,108,255,.055), transparent 35%); }
        .block-container { max-width: 1180px; padding-top: 2rem; padding-bottom: 4rem; }
        [data-testid="stSidebar"] { border-right: 1px solid var(--app-border); }
        [data-testid="stSidebar"] .block-container { padding-top: 1.6rem; }
        [data-testid="stHeader"] { background: transparent; }
        .app-brand { display:flex; align-items:center; gap:.8rem; margin:.25rem 0 1.8rem; }
        .app-brand__icon { width:42px; height:42px; padding:9px; color:white; background:linear-gradient(135deg,#6374ff,#8a5cff); border-radius:13px; box-shadow:0 8px 24px rgba(91,108,255,.28); }
        .app-brand__icon svg, .app-icon svg { width:100%; height:100%; display:block; }
        .app-brand__name { font-size:1.05rem; font-weight:750; line-height:1.2; }
        .app-brand__tag { color:var(--app-muted); font-size:.76rem; margin-top:.2rem; }
        .app-hero { padding:1.5rem 1.6rem; border:1px solid var(--app-border); border-radius:22px; background:linear-gradient(135deg,rgba(91,108,255,.13),rgba(138,92,255,.045)); margin-bottom:1.4rem; }
        .app-eyebrow { color:#7f8cff; font-size:.76rem; font-weight:750; letter-spacing:.12em; text-transform:uppercase; margin-bottom:.55rem; }
        .app-hero h1 { font-size:clamp(1.75rem,4vw,2.65rem); line-height:1.12; margin:0 0 .65rem; }
        .app-hero p { color:var(--app-muted); max-width:720px; margin:0; line-height:1.7; }
        .app-section-title { display:flex; align-items:center; gap:.7rem; margin:1rem 0 .8rem; }
        .app-section-title .app-icon { width:34px; height:34px; padding:7px; color:#7180ff; background:var(--app-primary-soft); border-radius:10px; }
        .app-section-title h2 { font-size:1.12rem; margin:0; }
        .app-stat-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:.85rem; margin:.8rem 0 1.2rem; }
        .app-stat { padding:1.05rem 1.1rem; border:1px solid var(--app-border); border-radius:16px; background:rgba(128,138,164,.045); }
        .app-stat__label { color:var(--app-muted); font-size:.78rem; }
        .app-stat__value { font-size:1.45rem; font-weight:760; margin-top:.25rem; }
        .app-note { display:flex; gap:.8rem; padding:1rem; border:1px solid var(--app-border); border-radius:15px; background:rgba(128,138,164,.04); margin:.8rem 0; }
        .app-note .app-icon { width:30px; min-width:30px; height:30px; padding:6px; color:#7180ff; background:var(--app-primary-soft); border-radius:9px; }
        .app-note strong { display:block; margin-bottom:.15rem; }
        .app-note span { color:var(--app-muted); font-size:.88rem; line-height:1.5; }
        .app-source { display:inline-block; padding:.38rem .62rem; margin:.2rem .25rem .2rem 0; border:1px solid var(--app-border); border-radius:999px; color:var(--app-muted); font-size:.78rem; }
        [data-testid="stFileUploader"] { border:1px dashed rgba(112,127,255,.55); border-radius:18px; padding:.35rem; background:rgba(91,108,255,.035); }
        [data-testid="stChatMessage"] { border:1px solid var(--app-border); border-radius:18px; padding:.25rem .45rem; background:rgba(128,138,164,.035); }
        [data-testid="stChatInput"] { border-radius:16px; }
        .stButton > button { border-radius:11px; min-height:2.65rem; font-weight:650; }
        @media (max-width: 720px) {
            .block-container { padding:1.1rem .9rem 4rem; }
            .app-stat-grid { grid-template-columns:1fr; }
            .app-hero { padding:1.2rem; border-radius:17px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_brand():
    st.markdown(
        f"""
        <div class="app-brand">
            <div class="app-brand__icon">{icon("brand")}</div>
            <div>
                <div class="app-brand__name">KnowFlow</div>
                <div class="app-brand__tag">个人知识库助手</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero(eyebrow: str, title: str, description: str):
    st.markdown(
        f"""
        <section class="app-hero">
            <div class="app-eyebrow">{html.escape(eyebrow)}</div>
            <h1>{html.escape(title)}</h1>
            <p>{html.escape(description)}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_section_title(icon_name: str, title: str):
    st.markdown(
        f"""
        <div class="app-section-title">
            <div class="app-icon">{icon(icon_name)}</div>
            <h2>{html.escape(title)}</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_note(icon_name: str, title: str, description: str):
    st.markdown(
        f"""
        <div class="app-note">
            <div class="app-icon">{icon(icon_name)}</div>
            <div><strong>{html.escape(title)}</strong><span>{html.escape(description)}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_stats(document_count: int, source_count: int, collection_name: str):
    st.markdown(
        f"""
        <div class="app-stat-grid">
            <div class="app-stat"><div class="app-stat__label">文本块</div><div class="app-stat__value">{document_count}</div></div>
            <div class="app-stat"><div class="app-stat__label">文件来源</div><div class="app-stat__value">{source_count}</div></div>
            <div class="app-stat"><div class="app-stat__label">向量集合</div><div class="app-stat__value">{html.escape(collection_name)}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
