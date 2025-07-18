FROM python:3.12

WORKDIR /backend

ENV PYTHONPATH=/backend

COPY ../requirements.txt .

RUN python -m pip install pip==23.2.1

RUN pip3 install -r requirements.txt --no-cache-dir

COPY ./backend ./