FROM python:3.10.8-slim-buster AS runner

RUN apt-get clean all
RUN apt-get update

RUN apt-get install -y unzip wget

# pascal
RUN apt-get install -y mono-complete mono-devel
# c++
RUN apt-get install -y gcc g++
# java
RUN apt-get install -y openjdk-11-jdk openjdk-11-jre
# pypy
RUN apt-get install -y pypy3
# lua
RUN apt-get install -y lua5.3
# cobol
RUN apt-get install -y gnucobol
# haskell
RUN apt-get install -y ghc ghc-prof ghc-doc
# fortran
RUN apt-get install -y gfortran
# rust
RUN apt install -y rustc


WORKDIR /pascal
RUN wget "http://pascalabc.net/downloads/PascalABCNETLinux.zip"
RUN unzip "PascalABCNETLinux.zip" "PascalABCNETLinux/*"
RUN echo '#! /bin/sh' >> /bin/pabcnetc
RUN echo 'mono /pascal/PascalABCNETLinux/pabcnetcclear.exe $1' >> /bin/pabcnetc
RUN chmod u+x /bin/pabcnetc

WORKDIR ../node
RUN wget "https://nodejs.org/dist/v18.16.1/node-v18.16.1-linux-x64.tar.xz"
RUN tar -xf node-v18.16.1-linux-x64.tar.xz
RUN mv node-v18.16.1-linux-x64/bin/node /bin/node


WORKDIR ../go
RUN wget "https://go.dev/dl/go1.20.5.linux-amd64.tar.gz" -O go.tar.gz
RUN tar -C /usr/local -xzf go.tar.gz
ENV PATH="$PATH:/usr/local/go/bin"

WORKDIR ..
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./main.py"]