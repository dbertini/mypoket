# Usa Python come immagine base
FROM python:3.10

# Imposta la directory di lavoro
WORKDIR /app

# Copia i file del bot
COPY my-poket-db.py .
COPY requirements.txt .

# Installa le dipendenze
RUN pip install --no-cache-dir -r requirements.txt

# Avvia il bot
CMD ["python", "my-poket-db.py"]
