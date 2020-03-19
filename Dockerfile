FROM matthewfeickert/docker-python3-ubuntu

USER root

RUN apt-get -y update && \
    apt-get -qq -y upgrade

RUN apt-get -y  install python3-tk  
# RUN apt-get -y install python3-pip


# RUN pip3 install --no-cache-dir --upgrade pip 

RUN pip3 install --no-cache-dir Pillow


# RUN apt-get install -y python3-tk && \
#     python3-imaging-tk && \
#     python3-reportlab

RUN apt-get -y autoclean && \
    apt-get -y autoremove && \
    rm -rf /var/lib/apt-get/lists/*

WORKDIR /cropper