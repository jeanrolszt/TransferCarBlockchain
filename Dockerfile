FROM python:latest
COPY . .
CMD [ "python","-u", "./main.py" ]