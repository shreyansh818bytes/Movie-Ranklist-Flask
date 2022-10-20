# Pull the python image
FROM python:3.8-alpine

# Copy requirements.txt
COPY ./requirements.txt /app/requirements.txt

# Switch working directory
WORKDIR /app

# Install python dependencies
RUN pip install -r requirements.txt

# Copy the code
COPY . /app

# Configure the container to run in an executed manner
ENTRYPOINT ["python"]
CMD ["app.py"]
