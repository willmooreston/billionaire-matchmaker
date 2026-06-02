FROM public.ecr.aws/lambda/python:3.14

RUN dnf install -y dejavu-fonts-all zlib-devel libjpeg-turbo-devel freetype-devel gcc python3-devel && dnf clean all

COPY lambda/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY lambda/ ${LAMBDA_TASK_ROOT}/

CMD ["handler.lambda_handler"]
