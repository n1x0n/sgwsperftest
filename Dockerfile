FROM python:3

MAINTAINER Fredrik Nygren "fredrik@phight.club"

RUN apt-get update && apt-get install -y vim

WORKDIR /root
ADD requirements.txt .
RUN pip install -r requirements.txt && rm requirements.txt
COPY config.ini download_data.py*  update_cert.sh upload_data.py report.html ./

ENTRYPOINT ["/bin/bash"]


