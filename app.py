import socket
import ssl
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import streamlit as st
from supabase import create_client


def _secret(*keys: str) -> str:
    for key in keys:
        value = st.secrets.get(key)
        if value:
            return str(value)

    supabase_section = st.secrets.get("supabase")
    if isinstance(supabase_section, dict):
        for key in keys:
            value = supabase_section.get(key)
            if value:
                return str(value)

    return ""

st.set_page_config(page_title="Simple DB Insert", page_icon="🗄️")
st.title("Simple Supabase Insert")


def _validate_supabase_url(url: str) -> str:
    cleaned = url.strip().strip("'\"").rstrip("/")
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
    url = _validate_supabase_url(_secret("SUPABASE_URL", "url"))
    key = _secret("SUPABASE_KEY", "key").strip()
    if not key:
        raise ValueError("Set SUPABASE_KEY in Streamlit secrets.")
    return create_client(url, key)


def run_connection_diagnostics() -> list[str]:
    notes: list[str] = []
    raw_url = _secret("SUPABASE_URL", "url")
    key = _secret("SUPABASE_KEY", "key").strip()

    if not raw_url:
        notes.append("❌ SUPABASE_URL is missing from Streamlit secrets.")
        return notes

    notes.append("✅ SUPABASE_URL found in secrets.")
    parsed = urlparse(raw_url.strip().strip("'\"").rstrip("/"))
    host = parsed.hostname or ""
    notes.append(f"ℹ️ Parsed host: `{host or 'unknown'}`")

    if not key:
        notes.append("❌ SUPABASE_KEY is missing from Streamlit secrets.")
        return notes
    notes.append("✅ SUPABASE_KEY found in secrets.")

    try:
        valid_url = _validate_supabase_url(raw_url)
        notes.append(f"✅ URL validation passed: `{valid_url}`")
    except Exception as exc:
        notes.append(f"❌ URL validation failed: {exc}")
        return notes

    try:
        addr_info = socket.getaddrinfo(host, 443)
        ip = addr_info[0][4][0]
        notes.append(f"✅ DNS lookup passed. First resolved IP: `{ip}`")
    except Exception as exc:
        notes.append(f"❌ DNS lookup failed: {exc}")
        return notes

    try:
        with socket.create_connection((host, 443), timeout=5):
            notes.append("✅ TCP connection to host:443 succeeded.")
    except Exception as exc:
        notes.append(f"❌ TCP connection failed: {exc}")
        return notes

    try:
        request = Request(
            f"{valid_url}/rest/v1/",
            headers={
                "apikey": key,
                "Authorization": f"Bearer {key}",
            },
        )
        with urlopen(request, context=ssl.create_default_context(), timeout=8) as response:
            notes.append(
                f"✅ REST endpoint reachable. HTTP status: {response.status}."
            )
    except Exception as exc:
        notes.append(f"❌ REST API request failed: {exc}")

    return notes


st.write("Enter a user and click **Insert**.")

with st.expander("Debug database connection"):
    st.caption(
        "Run focused diagnostics for URL format, DNS resolution, network reachability, and Supabase REST access."
    )
    if st.button("Run connection diagnostics"):
        for item in run_connection_diagnostics():
            st.write(item)

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
