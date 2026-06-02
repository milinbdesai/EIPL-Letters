"""Supabase client singletons + storage helpers."""
from __future__ import annotations
import streamlit as st
from supabase import create_client, Client
import uuid, mimetypes


@st.cache_resource
def _client(key_type: str) -> Client:
    cfg = st.secrets["supabase"]
    key = cfg["service_key"] if key_type == "service" else cfg["anon_key"]
    return create_client(cfg["url"], key)


def sb() -> Client:
    """Service-role client. Used because app already gates auth at login."""
    return _client("service")


def bucket() -> str:
    return st.secrets["supabase"]["storage_bucket"]


def upload_bytes(path_prefix: str, filename: str, data: bytes, content_type: str | None = None) -> str:
    """Upload bytes to storage. Returns public URL."""
    if not content_type:
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    safe_name = f"{path_prefix.strip('/')}/{uuid.uuid4().hex[:8]}_{filename}"
    sb().storage.from_(bucket()).upload(
        safe_name,
        data,
        {"content-type": content_type, "upsert": "true"},
    )
    return sb().storage.from_(bucket()).get_public_url(safe_name)


def delete_object_by_url(url: str) -> None:
    """Best-effort delete a stored object given its public URL."""
    try:
        marker = f"/object/public/{bucket()}/"
        if marker in url:
            key = url.split(marker, 1)[1]
            sb().storage.from_(bucket()).remove([key])
    except Exception:
        pass
