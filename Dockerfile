FROM python:3.8-slim

# streamlit-specific commands
RUN mkdir -p ~/.streamlit
RUN bash -c 'echo -e "\
    [server]\n\
    headless = true\n\
    port = $PORT\n\
    enableCORS = false\n\
    " > ~/.streamlit/config.toml'

# copy over and install packages
COPY requirements.txt ./app/requirements.txt
RUN pip3 install -r app/requirements.txt

# copy workspace over to /app
COPY . /app
WORKDIR /app

CMD ["sh", "-c", "streamlit run --server.port $PORT app.py"]
