# PetStory API — container só da pasta api (frontend na Vercel).
# Compose: docker compose up -d   (ou: docker compose up --build)
# Ou run:  docker run -p 8000:8000 --env-file api/.env \
#            -v $(pwd)/api/data:/app/data -v $(pwd)/api/uploads:/app/uploads petstory-api

FROM python:3.13-slim

WORKDIR /app

COPY api/ /app/

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
