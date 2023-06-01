#python 3.11 image
FROM python:3.11-bullseye

#install rsync 
RUN apt-get update && \
    apt-get -y install rsync

#install tree
RUN apt-get update && \
    apt-get -y install tree

#copy over src folder

COPY src /src
COPY requirements.txt /requirements.txt

#echo the variables that were passed down from the action.yml file
#RUN echo $token
#RUN echo $config

#copy over entrypoint.sh 
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]