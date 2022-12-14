FROM python:3.11
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONBUFFERED 1

# install ffmpeg
RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get install -y ffmpeg


WORKDIR /speech-recognition-bot

ADD . /speech-recognition-bot

COPY ./requirements.txt /speech-recognition-bot/requirements.txt

RUN pip install -r requirements.txt

COPY . /speech-recognition-bot
CMD ["python"]