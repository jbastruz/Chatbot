import pandas as pd  # Import the pandas library for data manipulation
import streamlit_authenticator as stauth  # Import the streamlit_authenticator library for user authentication
from yaml.loader import SafeLoader  # Import the SafeLoader from the yaml.loader module for loading YAML data safely
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage  # Import the datetime module for working with dates and times
import pytz as tz  # Import the pytz module for working with time zones
import streamlit as st  # Import the streamlit library for creating web apps
import yaml  # Import the yaml library for working with YAML files
import os  # Import the os module for interacting with the operating system

UPLOAD_DIRECTORY = os.path.abspath("Data")

with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

name, authentication_status, username = authenticator.login('main', fields = {'Form name':'Chatbot ASTRUZ', 'Username':'Nom d\'utilisateur', 'Password':'Mot de passe', 'Login':'Connexion'})

if authentication_status:
    st.markdown("<h1 style='text-align: center;'>Suivi d'Intervention</h1>", unsafe_allow_html=True)

    with st.container(border=True) :
        st.session_state.Miss = st.selectbox(
        " ".join(('Missions de ', name,':')),
        st.session_state.df[st.session_state.df["Inter"] == username]['KEY'].unique(),
        index=0)

    col1, col2 = st.columns([4, 1])
    with col1:
        st.session_state.Notes = st.text_input('Notes de l\'intervenant :', placeholder = "Notez vos observations...")
    with col2:
        container = st.container(border=True)
        with container:
            st.markdown(f"""Montant à payer: \n :red[***{st.session_state.df[st.session_state.df['KEY']==st.session_state.Miss]["total_ttc"].values[0]}€***]""")
            print(st.session_state.df[st.session_state.df['KEY']==st.session_state.Miss]["total_ttc"])
        #st.session_state.time = st.number_input("Prix :", min_value = 0.0, max_value = 24.0, value = "min", step = 0.5, help = "Prix à faire payer", disabled = True)
    uploaded_file = st.file_uploader("Ajoute des photos :", accept_multiple_files=True, help="Ajoutez des photos de l'intervention")

    st.button('Mettre à jour', on_click = MaJ, use_container_width = True)

    with st.sidebar:
        st.title("Réglages :")
        st.button('déconnexion', on_click=deco, key = 'unrendered', use_container_width = True)