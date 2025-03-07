import streamlit as st

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

container = st.container(border=True)

def login():
    if container.text_input("Username"):
        if container.text_input("Password", type="password"):
            if container.button("log in", icon=":material/login:"):
                st.session_state.logged_in = True
                st.rerun()

def logout():
    if container.button("log out", icon=":material/logout:"):
        st.session_state.logged_in = False
        st.rerun()


log = st.Page(
    login,
    title="Log in",
    icon=":material/account_circle:",
)

lout = st.Page(
    logout,
    title="Log out",
    icon=":material/logout:",
)


deshboards = st.Page(
    page="pages/deshboards.py",
    title="Dados Modbus",
    icon=":material/bar_chart:",
)

if st.session_state.logged_in:
    pg = st.navigation(
        {
            "Account": [lout],
            "Pages": [deshboards],
        }
    )
else:
    pg = st.navigation([log])

pg.run()