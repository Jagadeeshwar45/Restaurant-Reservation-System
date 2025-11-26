import streamlit as st
from agent import handle_user_message
from reservations import list_reservations
from pathlib import Path

st.set_page_config(page_title='GoodFoods Reservation Assistant', layout='wide')
st.title("🧀 GoodFoods — Reservation Assistant")

# Initialize session state variables
if 'history' not in st.session_state:
    st.session_state.history = []
if 'user_input' not in st.session_state:
    st.session_state.user_input = ""

col1, col2 = st.columns([3,1])

with col1:
    # Get user input
    user_input = st.text_input(
        "Ask me to book, find, or cancel a reservation",
        value=st.session_state.user_input,
        key='user_input_widget'
    )
    
    send = st.button("Send")

    if send and user_input.strip():
        st.session_state.history.append({"role":"user","text":user_input})
        reply = handle_user_message(user_input)
        st.session_state.history.append({"role":"assistant","text":reply})
        st.session_state.user_input = ""
        st.rerun()  # Rerun to clear the input

    for msg in st.session_state.history[::-1]:
        if msg['role']=='assistant':
            st.markdown(f"""
            <div style="background-color:#F8F9FA;padding:12px;border-radius:10px;border:1px solid #DDD;">
            {msg['text']}
            </div>
            """, unsafe_allow_html=True)

        else:
            st.markdown(f"**You:** {msg['text']}")

with col2:
    st.subheader("Admin")
    if st.button("Show recent reservations"):
        rows = list_reservations()
        if not rows:
            st.write("No reservations yet.")
        else:
            for r in rows:
                st.write(f"#{r['id']} | Rest {r['restaurant_id']} | {r['datetime']} | seats {r['seats']} | {r['name']} | {r['status']}")
    st.markdown("---")
    st.write("Dataset: data/restaurants.json")
    if Path('../data/restaurants.json').exists():
        st.write("Restaurants loaded.")
    st.write("Tip: try `'Book a table for 4 tomorrow at 7pm'` or `'Find Italian for 6'`")




    #   streamlit run app/streamlit_app.py
