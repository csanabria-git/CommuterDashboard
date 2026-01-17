FROM public.ecr.aws/lambda/python:3.12

# Install underground
RUN pip install --no-cache-dir underground

# Copy handler
COPY app.py ${LAMBDA_TASK_ROOT}

CMD ["app.handler"]
