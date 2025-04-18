ARG FUNCTION_DIR="/app"
FROM python:3.13-slim
ARG FUNCTION_DIR
RUN mkdir -p ${FUNCTION_DIR} && \
    echo "sparksam:x:1000:1000:sparksam:${FUNCTION_DIR}:" > /etc/passwd && \
    echo "sparksam:x:1000:" > /etc/group && \
    chown -R sparksam:sparksam ${FUNCTION_DIR}
USER sparksam
COPY requirements.txt ${FUNCTION_DIR}/requirements.txt
WORKDIR ${FUNCTION_DIR}
RUN pip install -r requirements.txt
COPY . /app
CMD ["python", "src/app.py"]