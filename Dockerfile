FROM ubuntu:20.04

ENV TZ=Europe
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install basic dependencies
RUN apt-get update && \
    apt-get install -y nano git ssh unzip wget python3 python3-pip python3-dev -y

########################################################################################################################
# Setup & Enable SSH
########################################################################################################################
RUN service ssh start && mkdir /root/.ssh && chmod 700 /root/.ssh && \
    ssh-keygen -f /root/.ssh/id_rsa -t rsa -N '' -C root@$(hostname) && mkdir -p /shared/ssh/ && \
    cat /root/.ssh/id_rsa.pub >> /shared/ssh/authorized_keys

RUN mkdir /opt/cquencer
WORKDIR /opt/cquencer
COPY . ./
ENV PYTHONPATH "$(pwd)"
ENV PATH "/opt/cquencer:${PATH}"

########################################################################################################################
# Change /bin/sh link from /bin/dash to /bin/bash
########################################################################################################################
RUN mv /bin/sh /bin/sh.orig && ln -s /bin/bash /bin/sh

########################################################################################################################
# Install OpenNMT-py and python dependencies
########################################################################################################################
RUN pip3 install OpenNMT-py==1.2.0 
RUN pip3 install -r requirements.txt

VOLUME /opt/cquencer
