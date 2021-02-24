FROM jupyter/datascience-notebook:latest

COPY ./requirements.txt ./

RUN pip install -r requirements.txt

USER root

WORKDIR /home/jovyan

RUN apt-get update
RUN apt-get install software-properties-common -y
RUN add-apt-repository ppa:ethereum/ethereum -y
RUN apt-get install solc -y
RUN pip install py-solc-x
RUN pip install uniswap-python
RUN pip install eth-brownie


