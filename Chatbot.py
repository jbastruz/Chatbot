import pandas as pd # Import the pandas library for data manipulation
import streamlit_authenticator as stauth # Import the streamlit_authenticator library for user authentication
from yaml.loader import SafeLoader # Import the SafeLoader from the yaml.loader module for loading YAML data safely
from mistralai.client import MistralClient # Import the MistralClient from the mistralai.client module
from mistralai.models.chat_completion import ChatMessage # Import the ChatMessage from the mistralai.models.chat_completion module
import pytz as tz # Import the pytz module for working with time zones
import streamlit as st # Import the streamlit library for creating web apps
import yaml # Import the yaml library for working with YAML files
import os # Import the os module for interacting with the operating system
from dotenv import load_dotenv # Import the load_dotenv function from the dotenv module
from streamlit_option_menu import option_menu # Import the option_menu function from the streamlit_option_menu module
import time # Import the time module for working with time

st.set_page_config(
    page_title="Chatruz",
    page_icon= 'Data/electron.png'
)
UPLOAD_DIRECTORY = os.path.abspath("Data")
load_dotenv()

# Open the 'config.yaml' file and load its content safely
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# If the upload directory does not exist, create it
if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

CSV_FILE = "Data/chat_history.csv"

# Try to read the CSV file, if it doesn't exist, create an empty DataFrame
try:
    chat_history_df = pd.read_csv(CSV_FILE)
except FileNotFoundError:
    chat_history_df = pd.DataFrame(columns=["Role", "Content", "ChatID", 'User'])

# Authenticate the user
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

# Check if the Mistral API key is set, if not, show an info message and stop
if not os.getenv("MISTRAL_API_KEY"):
    st.info("Please add your Mistral API key in your environment variables to continue.")
    st.stop()
else:
    mistral_api_key = os.getenv("MISTRAL_API_KEY")

# Define models dictionary
models = {
    "Mistral-tiny": "open-mistral-7b", 
    "Mistral-small": "open-mixtral-8x7b", 
    "Mistral-medium": "mistral-medium-2312", 
    "Mistral-large": "mistral-large-latest"
}

# Create Mistral client with API key
client = MistralClient(api_key=mistral_api_key)

# Reset conversation state
def reset_conv():
    st.session_state["ChatID"] = time.time()
    st.session_state["messages"] = [{"role": "assistant", "content": f"Bonjour {name}, comment puis-je vous aider?"}]
    st.session_state["history"] = [ChatMessage(role= "system", content= "Vous êtes un assistant préparé pour aider l'utilisateur")]

# Save chat history
def save_history():
    df = pd.read_csv(CSV_FILE)
    df =  df[df.ChatID != st.session_state.ChatID] 
    df.to_csv(CSV_FILE, index=False)
    df = pd.DataFrame(st.session_state.messages)
    df['ChatID'] = st.session_state.ChatID
    df['User'] = username
    df.to_csv('Data/chat_history.csv', mode='a', header=False, index=False)

# Disconnect the user
def disconnect():
    authenticator.logout('logout', 'unrendered')

# Get the button label based on chat history
def get_button_label(chat_df, chat_id):
    first_message = chat_df[(chat_df["ChatID"] == chat_id) & (chat_df["Role"] == "user")].iloc[0]["Content"]
    return f"Chat {str(chat_id)[5:10]}: {' '.join(first_message.split()[:5])}..."

name, authentication_status, username = authenticator.login('main', fields = {'Form name':'Chatbot ASTRUZ', 'Username':'Nom d\'utilisateur', 'Password':'Mot de passe', 'Login':'Connexion'})

if authentication_status:

    with st.sidebar:
        st.title("🤖💬 Chatruz 🤖💬")
        st.caption("By Jean-Baptiste ASTRUZ")
        with st.expander("Modèles"):
            selector = option_menu(None ,["Mistral-tiny", 'Mistral-small', 'Mistral-medium', "Mistral-large"], 
                icons=['star', 'star-half', 'star-fill', 'stars'], menu_icon="chat-dots", default_index=1)
        st.button("Se deconnecter", on_click=disconnect, use_container_width=True)
        col1, col2 = st.columns([4, 4])
        with col1:
            st.button("Recommencer la conversation", on_click=reset_conv, use_container_width=True)
        with col2:
            st.button("Sauvegarder la conversation", on_click=save_history, use_container_width=True)
        st.header("Historique de conversation:")

    if "messages" not in st.session_state:
        st.session_state["ChatID"] = time.time()
        st.session_state["messages"] = [{"role": "assistant", "content": f"Bonjour {name}, comment puis-je vous aider?"}]
        st.session_state["history"] = [ChatMessage(role= "system", content= "Vous êtes un assistant compétent qui avait proposé votre aide à l'utilisateur")]

    for chat_id in chat_history_df[chat_history_df["User"] == username]["ChatID"].unique():
        button_label = get_button_label(chat_history_df, chat_id)
        if st.sidebar.button(button_label, key=chat_id, use_container_width=True):
            st.session_state["ChatID"] = chat_id
            loaded_chat = chat_history_df[chat_history_df["ChatID"] == chat_id]
            st.session_state["history"] = [ChatMessage(role= "system", content= "Vous êtes un assistant compétent qui avait proposé votre aide à l'utilisateur")]
            st.session_state["history"].extend(ChatMessage(role= row["Role"], content= row["Content"]) for _, row in loaded_chat.iterrows())
            st.session_state["history"].pop(0)
            st.session_state["messages"] = [{"role": row["Role"], "content": row["Content"]} for _, row in loaded_chat.iterrows()]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input():
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.history.append(ChatMessage(role= "user", content= prompt))
        print(st.session_state.history)
        st.chat_message("user").write(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            for reponse in client.chat_stream(
                            model=models[selector],
                            messages=st.session_state.history
                        ) :
                full_response += (reponse.choices[0].delta.content or "")
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
            st.session_state.history.append(ChatMessage(role="assistant", content=full_response))
            st.session_state.messages.append({"role": "assistant", "content": full_response})