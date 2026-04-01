FROM python:3.11-slim

WORKDIR /app

# Install agent-generator from the repo (includes all production infrastructure)
COPY agent_generator_pkg/ /tmp/agent-generator-pkg/
RUN pip install --no-cache-dir /tmp/agent-generator-pkg/ && rm -rf /tmp/agent-generator-pkg/

# Install web dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=7860
EXPOSE 7860

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
