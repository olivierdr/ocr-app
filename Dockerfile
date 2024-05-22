FROM python:3.9

WORKDIR /usr/home

# Upgrade pip
RUN pip install --upgrade pip

COPY requirements.txt /tmp/requirements.txt

RUN pip install -r /tmp/requirements.txt \
        && rm -r /tmp/requirements.txt 


