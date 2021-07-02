FROM botrequirements

WORKDIR /bot
COPY ./bot /bot

RUN export PYTHONPATH=/bot/components/:$PYTHONPATH

#USER root

RUN find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf

#USER 1001