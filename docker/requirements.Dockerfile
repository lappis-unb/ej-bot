FROM  rasa/rasa:2.2.10

USER root

RUN apt update && apt install -y
RUN python -m pip install --upgrade pip

WORKDIR /tmp
COPY ./docker/ /tmp

RUN pip install --no-cache-dir -r /tmp/dependencies/requirements-development.txt
#    pip install --use-deprecated=legacy-resolver --no-cache-dir -r /tmp/dependencies/x-requirements.txt
RUN python -c "import nltk; nltk.download('stopwords');"
RUN python -m spacy download pt_core_news_sm

#USER 1001