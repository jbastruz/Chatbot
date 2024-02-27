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

COPY . ./

RUN pip install -r requirements.txt
#Copy files to your container
COPY Intervention.py ./Intervention.py
EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "Intervention.py", "--server.enableCORS=false"]