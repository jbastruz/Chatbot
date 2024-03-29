FROM python:3.12.1
# Using Layered approach for the installation of requirements
WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
RUN apt-get -y update
RUN apt -y install nano
RUN export MISTRAL_API_KEY="***"

COPY . ./

RUN pip install -r requirements.txt
#Copy files to your container
COPY Chatbot.py ./Chatbot.py
EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "Chatbot.py", "--server.enableCORS", "false", "--server.enableXsrfProtection", "false"]

#nativefier --name Audiofy https://share.streamlit.io/sree369nidhi/audiobook/main/pdf_to_audiobook.py --platform windows
#nativefier --name '<you .exe name>' '<your streamlit sharing website url>' --platform <'windows' or 'mac' or 'linux'>
