FROM python:3.8-slim

# streamlit-specific commands
RUN mkdir -p ~/.streamlit
RUN bash -c 'echo -e "\
    [server]\n\
    headless = true\n\
    port = $PORT\n\
    enableCORS = false\n\
    " > ~/.streamlit/config.toml'

RUN python -m pip install --upgrade pip

# copy over and install packages
COPY requirements.txt ./app/requirements.txt
RUN pip install -r app/requirements.txt

# copy workspace over to /app
COPY . /app
WORKDIR /app

CMD ["sh", "-c", "streamlit run --server.port $PORT app.py"]
