import pandas as pd  # Import the pandas library for data manipulation
import streamlit_authenticator as stauth  # Import the streamlit_authenticator library for user authentication
from yaml.loader import SafeLoader  # Import the SafeLoader from the yaml.loader module for loading YAML data safely
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage  # Import the datetime module for working with dates and times
import pytz as tz  # Import the pytz module for working with time zones
import streamlit as st  # Import the streamlit library for creating web apps
import yaml  # Import the yaml library for working with YAML files
import os  # Import the os module for interacting with the operating system
from streamlit_option_menu import option_menu
import time
import csv

UPLOAD_DIRECTORY = os.path.abspath("Data")

with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

CSV_FILE = "Data/chat_history.csv"
try:
    chat_history_df = pd.read_csv(CSV_FILE)
except FileNotFoundError:
    chat_history_df = pd.DataFrame(columns=["Role", "Content", "ChatID", 'User'])

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

if not os.getenv("MISTRAL_API_KEY"):
    st.info("Please add your Mistral API key in your environment variables to continue.")
    st.stop()
else :
    mistral_api_key = os.getenv("MISTRAL_API_KEY")

models = {"Mistral-tiny":"open-mistral-7b", "Mistral-small":"open-mixtral-8x7b", "Mistral-medium":"mistral-medium-2312", "Mistral-large (WIP)":"mistral-large-latest"}
client = MistralClient(api_key=mistral_api_key)

def reset_conv():
    st.session_state["ChatID"] = time.time()
    st.session_state["messages"] = [{"role": "assistant", "content": f"Bonjour {name}, comment puis-je vous aider?"}]
    st.session_state["history"] = [ChatMessage(role= "system", content= "Vous êtes un assistant préparé pour aider l'utilisateur")]
    st.session_state["history"].append(ChatMessage(role= "assistant", content= f"Bonjour {name}, comment puis-je vous aider?"))

def save_history():
    
    df = pd.read_csv(CSV_FILE)
    df =  df[df.ChatID != st.session_state.ChatID] 
    df.to_csv(CSV_FILE, index=False)
    df = pd.DataFrame(st.session_state.messages)
    df['ChatID'] = st.session_state.ChatID
    df['User'] = username
    df.to_csv('Data/chat_history.csv', mode='a', header=False, index=False)

def disconnect():
    authenticator.logout('logout', 'unrendered')

def get_button_label(chat_df, chat_id):
    first_message = chat_df[(chat_df["ChatID"] == chat_id) & (chat_df["Role"] == "user")].iloc[0]["Content"]
    return f"Chat {str(chat_id)[5:10]}: {' '.join(first_message.split()[:5])}..."

name, authentication_status, username = authenticator.login('main', fields = {'Form name':'Chatbot ASTRUZ', 'Username':'Nom d\'utilisateur', 'Password':'Mot de passe', 'Login':'Connexion'})

if authentication_status:
    with st.sidebar:
        st.title("🤖💬 Chatruz 🤖💬")
        st.caption("By Jean-Baptiste ASTRUZ")
        st.header("Modèles:")
        selector = option_menu(None ,["Mistral-tiny", 'Mistral-small', 'Mistral-medium', 'Mistral-large (WIP)'], 
            icons=['star', 'star-half', 'star-fill', 'stars'], menu_icon="chat-dots", default_index=1)
        st.divider()
        st.button("Se deconnecter", on_click=disconnect, use_container_width=True)
        col1, col2 = st.columns([4, 4])
        with col1:
            st.button("Recommencer la conversation", on_click=reset_conv)
        with col2:
            st.button("Sauvegarder la conversation", on_click=save_history)
        st.header("Historique de conversation:")

    if "messages" not in st.session_state:
        st.session_state["ChatID"] = time.time()
        st.session_state["messages"] = [{"role": "assistant", "content": f"Bonjour {name}, comment puis-je vous aider?"}]
        st.session_state["history"] = [ChatMessage(role= "system", content= "Vous êtes un assistant compétent qui avait proposé votre aide à l'utilisateur")]
        st.session_state["history"].append(ChatMessage(role= "assistant", content= f"Bonjour {name}, comment puis-je vous aider?"))

    for chat_id in chat_history_df[chat_history_df["User"] == username]["ChatID"].unique():
        button_label = get_button_label(chat_history_df, chat_id)
        if st.sidebar.button(button_label, key=chat_id, use_container_width=True):
            st.session_state["ChatID"] = chat_id
            loaded_chat = chat_history_df[chat_history_df["ChatID"] == chat_id]
            st.session_state["history"] = [ChatMessage(role= "system", content= "Vous êtes un assistant compétent qui avait proposé votre aide à l'utilisateur")]
            st.session_state["history"].extend(ChatMessage(role= row["Role"], content= row["Content"]) for _, row in loaded_chat.iterrows())
            st.session_state["messages"] = [{"role": row["Role"], "content": row["Content"]} for _, row in loaded_chat.iterrows()]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input():
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.history.append(ChatMessage(role= "user", content= prompt))
        print(st.session_state.messages)
        st.chat_message("user").write(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            for response in client.chat_stream(
                model=models[selector],
                messages=st.session_state.history
            ):
                full_response += (response.choices[0].delta.content or "")
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
            st.session_state.history.append(ChatMessage(role="assistant", content=full_response))
            st.session_state.messages.append({"role": "assistant", "content": full_response})