import socket
from urllib.parse import urlparse

import httpx
import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Supabase Connection MVP", page_icon="🗄️")
st.title("Supabase Connection MVP")


def get_secret(name: str) -> str:
    value = st.secrets.get(name, "")
    return str(value).strip()


def get_supabase():
    url = get_secret("SUPABASE_URL")
    key = get_secret("SUPABASE_KEY")
    return create_client(url, key)


def show_error(exc: Exception) -> None:
    st.error("Request failed")
    st.write("**Exception type:**", type(exc).__name__)
    st.write("**Exception message:**", str(exc))


supabase_url = get_secret("SUPABASE_URL")
supabase_key = get_secret("SUPABASE_KEY")
parsed_url = urlparse(supabase_url)
hostname = parsed_url.hostname or ""

st.header("Secrets / debug info")
st.write("**SUPABASE_URL (repr):**", repr(supabase_url))
st.write("**Hostname:**", hostname)
st.write("**SUPABASE_KEY present:**", bool(supabase_key))

st.header("DNS test")
if st.button("Run DNS test"):
    try:
        if not hostname:
            raise ValueError("Could not parse hostname from SUPABASE_URL")
        dns_result = socket.getaddrinfo(hostname, 443)
        st.success("DNS lookup succeeded")
        st.write(dns_result)
    except Exception as exc:
        show_error(exc)

st.header("HTTP test")
if st.button("Run HTTP test"):
    try:
        if not supabase_url:
            raise ValueError("SUPABASE_URL is empty")
        endpoint = f"{supabase_url.rstrip('/')}/rest/v1/"
        response = httpx.get(endpoint, timeout=10)
        st.write("**Endpoint:**", endpoint)
        st.write("**Status code:**", response.status_code)
        st.write("**Body preview:**", response.text[:300])
        if response.status_code < 500:
            st.success("HTTP request completed")
        else:
            st.warning("HTTP endpoint reachable, but returned server error")
    except Exception as exc:
        show_error(exc)

st.header("Real select test")
if st.button("Run real select test"):
    try:
        supabase = get_supabase()
        result = supabase.table("app_users").select("id").limit(1).execute()
        st.success("Supabase select query succeeded")
        st.write(result.data)
    except Exception as exc:
        show_error(exc)

st.header("Insert test form")
with st.form("insert_form"):
    full_name = st.text_input("Full name")
    email = st.text_input("Email")
    role = st.text_input("Role", value="user")
    submitted = st.form_submit_button("Insert user")

if submitted:
    try:
        normalized_email = email.strip().lower()
        if not normalized_email:
            raise ValueError("Email is required")

        payload = {
            "full_name": full_name.strip() or None,
            "email": normalized_email,
            "role": role.strip() or "user",
        }
        supabase = get_supabase()
        result = supabase.table("app_users").insert(payload).execute()
        st.success("Insert succeeded")
        st.write(result.data)
    except Exception as exc:
        show_error(exc)

st.header("Select up to 5 rows")
if st.button("Fetch up to 5 users"):
    try:
        supabase = get_supabase()
        result = (
            supabase.table("app_users")
            .select("id,email,full_name,role,created_at")
            .limit(5)
            .execute()
        )
        st.success("Select succeeded")
        st.write(result.data)
    except Exception as exc:
        show_error(exc)
