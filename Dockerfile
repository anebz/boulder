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
COPY requirements.txt ./requirements.txt
RUN pip3 install -r requirements.txt

# copying everything over, including the .csv
COPY . /

CMD ["sh", "-c", "streamlit run --server.port $PORT app.py"]
