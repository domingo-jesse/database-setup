import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Simple DB Insert", page_icon="🗄️")
st.title("Simple Supabase Insert")


def get_supabase_client():
    url = str(st.secrets.get("SUPABASE_URL", "")).strip()
    key = str(st.secrets.get("SUPABASE_KEY", "")).strip()
    if not url or not key:
        raise ValueError("Set SUPABASE_URL and SUPABASE_KEY in Streamlit secrets.")
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
