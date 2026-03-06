import streamlit as st
from core.bootstrap import init_system


# --------------------------------
# PAGE CONFIG
# --------------------------------

st.set_page_config(
    page_title="Personal Music Architect",
    page_icon="🎧",
    layout="wide"
)


# --------------------------------
# TITLE
# --------------------------------

st.title("🎧 Personal Music Architect")
st.caption("Your AI music assistant for building and managing playlists")


# --------------------------------
# INITIALIZE SYSTEM
# --------------------------------

if "system" not in st.session_state:
    st.session_state.system = init_system()

if "messages" not in st.session_state:
    st.session_state.messages = []


system = st.session_state.system
repo = system.repo


# --------------------------------
# SIDEBAR STATS
# --------------------------------

with st.sidebar:

    st.header("📊 Library Stats")

    try:

        total_tracks = repo.count_tracks()
        total_playlists = repo.count_playlists()
        total_artists = repo.count_artists()

        st.metric("Songs", total_tracks)
        st.metric("Playlists", total_playlists)
        st.metric("Artists", total_artists)

    except:
        st.write("Stats unavailable")

    st.divider()

    st.subheader("💡 Try asking")

    st.markdown("""
Create a sad playlist  
Create a nostalgic playlist  
Create a playlist with songs by Drake  
How many songs do I have in my library?  
List my playlists  
Add more songs  
""")


# --------------------------------
# CHAT HISTORY
# --------------------------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.write(message["content"])


# --------------------------------
# USER INPUT
# --------------------------------

prompt = st.chat_input("Ask your music assistant...")


if prompt:

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):

        with st.spinner("Thinking..."):

            try:

                result = system.session.handle(prompt)

                response = result.get("clarification_message")

                if not response:
                    response = result.get("error", "Request processed.")

            except Exception as e:

                response = f"⚠️ System error: {e}"

        st.write(response)

    st.session_state.messages.append({
        "role": "assistant",
        "content": response
    })