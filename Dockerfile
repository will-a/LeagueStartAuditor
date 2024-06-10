FROM python:3.12.4-alpine3.20
RUN apk add gcc g++ musl-dev
RUN python -m pip install --upgrade setuptools
ADD requirements.txt ./requirements.txt
RUN python -m pip install -r requirements.txt
ADD . ./
RUN python setup.py
EXPOSE 4444
CMD python main.py