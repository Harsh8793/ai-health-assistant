FROM python:3.10

# Set up environment
RUN apt-get update && apt-get install -y tesseract-ocr poppler-utils libglib2.0-0 libsm6 libxext6 libxrender-dev ffmpeg

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

COPY --chown=user . /app
RUN pip install --no-cache-dir -r requirements.txt

CMD ["streamlit", "run", "home.py", "--server.port=7860", "--server.address=0.0.0.0"]
