# Use python container image
FROM python:3.6-stretch

# Set the working directory of the image filesystem
WORKDIR /backend

# Copy the current directory to the working directory
ADD . /backend

# Install the python dependencies
RUN pip install -r requirements.txt
RUN pip install uWSGI

# Start the uWSGI
CMD ["uwsgi", "app.ini"]