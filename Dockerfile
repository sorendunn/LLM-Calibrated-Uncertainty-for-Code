# Use the official Python base image
FROM python:3.9

# Create a non-root user and set the working directory
RUN useradd --create-home appuser
WORKDIR /home/appuser

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY --chown=appuser:appuser . .

# Switch to the non-root user
USER appuser

# Run the shell script when the container starts
# CMD ["./run_gen_5.sh"]
CMD ["./run_simple.sh"]