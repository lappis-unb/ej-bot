FROM  rasa/rasa:3.6.6
USER root
RUN apt update && apt install build-essential -y
RUN python -m pip install --upgrade pip
COPY ./docker/ /tmp
RUN pip install -r /tmp/development-requirements.txt
WORKDIR /bot
