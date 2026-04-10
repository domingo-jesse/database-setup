import socket
from urllib.parse import urlparse

import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Simple DB Insert", page_icon="🗄️")
st.title("Simple Supabase Insert")


def _validate_supabase_url(url: str) -> str:
    cleaned = url.strip()
    if not cleaned:
        raise ValueError("Set SUPABASE_URL in Streamlit secrets.")

    if not (cleaned.startswith("http://") or cleaned.startswith("https://")):
        raise ValueError(
            "SUPABASE_URL must start with http:// or https:// (example: https://<project-ref>.supabase.co)."
        )

    parsed = urlparse(cleaned)
    if not parsed.netloc:
        raise ValueError(
            "SUPABASE_URL is invalid. Expected format: https://<project-ref>.supabase.co"
        )

    try:
        socket.getaddrinfo(parsed.hostname, 443)
    except socket.gaierror as exc:
        raise ConnectionError(
            f"Cannot resolve Supabase host '{parsed.hostname}'. Check SUPABASE_URL and DNS/network settings."
        ) from exc

    return cleaned


def get_supabase_client():
    url = _validate_supabase_url(str(st.secrets.get("SUPABASE_URL", "")))
    key = str(st.secrets.get("SUPABASE_KEY", "")).strip()
    if not key:
        raise ValueError("Set SUPABASE_KEY in Streamlit secrets.")
    return create_client(url, key)


st.write("Enter a user and click **Insert**.")

with st.form("insert_user_form"):
    full_name = st.text_input("Full name")
    email = st.text_input("Email")
    role = st.text_input("Role", value="user")
    submitted = st.form_submit_button("Insert")

if submitted:
    try:
        email_value = email.strip().lower()
        if not email_value:
            raise ValueError("Email is required.")

        payload = {
            "full_name": full_name.strip() or None,
            "email": email_value,
            "role": role.strip() or "user",
        }

        supabase = get_supabase_client()
        result = supabase.table("app_users").insert(payload).execute()

        st.success("Inserted successfully.")
        st.write(result.data)
    except Exception as exc:
        st.error(f"Insert failed: {exc}")
