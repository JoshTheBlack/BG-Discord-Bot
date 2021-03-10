FROM python:3

WORKDIR /usr/src/

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py main.py

cmd [ "cp", ".", "app/"]
cmd [ "python", "./main.py" ]