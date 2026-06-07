"""Thin convenience wrapper so pages can log activity in one line.

Usage:  from components.activity import log
        log("Created product", entity="product", entity_id=pid, detail=name)
"""
import streamlit as st
from .database import record_activity


def log(action: str, entity: str = "", entity_id=None, detail: str = ""):
    record_activity(
        username=st.session_state.get("username", "system"),
        full_name=st.session_state.get("full_name", ""),
        role=st.session_state.get("role", ""),
        action=action,
        entity=entity,
        entity_id=entity_id,
        detail=detail,
    )
