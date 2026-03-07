import streamlit as st

# ------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------

st.set_page_config(
    page_title="Personal Music Architect",
    page_icon="👽",
    layout="wide"
)

# ------------------------------------------------
# IMPORT BACKEND
# ------------------------------------------------

from core.bootstrap import init_system

# ------------------------------------------------
# CSS
# ------------------------------------------------

st.markdown("""
<style>

/* BACKGROUND */

.stApp {
    background-color: #00111a;
}

/* REMOVE WHITE AREA */

.block-container {
    padding-bottom: 0rem;
}

/* HIDE STREAMLIT HEADER */

header {visibility:hidden;}
footer {visibility:hidden;}

/* CENTER CONTENT WRAPPER */

.center-wrapper{
max-width:900px;
margin-left:auto;
margin-right:auto;
text-align:center;
margin-top:80px;
}

/* CONNECTED TEXT */

.connected{
color:#8a8a8a;
margin-top:10px;
}

/* SUGGESTIONS */

.suggestion-container{
display:flex;
justify-content:center;
gap:25px;
margin-top:40px;
}

.suggestion{
border:1px solid #1DB954;
color:#1DB954;
padding:10px 20px;
border-radius:30px;
font-size:14px;
}

/* CHAT AREA */

.chat-container{
max-width:900px;
margin:auto;
margin-top:40px;
}

/* USER MESSAGE */

.user-message{
background:#1DB954;
color:white;
padding:12px 18px;
border-radius:18px;
margin:10px 0;
width:fit-content;
margin-left:auto;
}

/* AI MESSAGE */

.ai-message{
background:#0c2a30;
color:white;
padding:12px 18px;
border-radius:18px;
margin:10px 0;
max-width:70%;
}

/* CHAT INPUT */

.stChatInputContainer{
background:#00111a;
}

.stChatInputContainer textarea{
border:2px solid #1DB954;
border-radius:30px;
background:#00111a;
color:white;
}

/* SEND BUTTON */

.stChatInputContainer button{
background:#1DB954;
color:white;
border-radius:50%;
}

.stChatInputContainer button:hover{
background:#1ed760;
}

</style>
""", unsafe_allow_html=True)

# ------------------------------------------------
# SYSTEM INIT
# ------------------------------------------------

if "system" not in st.session_state:
    st.session_state.system = init_system()

system = st.session_state.system

# ------------------------------------------------
# HEADER
# ------------------------------------------------

left, center, right = st.columns([1,2,1])

with center:
    st.image("assets/logo.png", width=380)

st.markdown(
"""
<div style="text-align:center;color:#8a8a8a;margin-top:10px">
Connected to Spotify
</div>
""",
unsafe_allow_html=True
)

# ------------------------------------------------
# SUGGESTIONS
# ------------------------------------------------

st.markdown("""
<div class="suggestion-container">

<div class="suggestion">
Create a playlist...?
</div>

<div class="suggestion">
Search in your library?
</div>

<div class="suggestion">
Modify a playlist?
</div>

</div>
""", unsafe_allow_html=True)

# ------------------------------------------------
# CHAT MEMORY
# ------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

# ------------------------------------------------
# CHAT HISTORY
# ------------------------------------------------

st.markdown('<div class="chat-container">', unsafe_allow_html=True)

for message in st.session_state.messages:

    if message["role"] == "user":

        st.markdown(
            f'<div class="user-message">{message["content"]}</div>',
            unsafe_allow_html=True
        )

    else:

        st.markdown(
            f'<div class="ai-message">👽 {message["content"]}</div>',
            unsafe_allow_html=True
        )

st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------
# CHAT INPUT
# ------------------------------------------------

prompt = st.chat_input("What do you want to listen to today?")

if prompt:

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    try:

        with st.spinner("Analyzing your music library..."):

            result = system.session.handle(prompt)

            response = result.get("clarification_message")

            if not response:
                response = result.get("error", "Done.")

    except Exception as e:

        response = f"Error: {e}"

    st.session_state.messages.append({
        "role": "assistant",
        "content": response
    })

    st.rerun()