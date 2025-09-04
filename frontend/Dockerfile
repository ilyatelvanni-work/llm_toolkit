FROM node:20-slim

WORKDIR /app

ARG REACT_APP_VERSION=3

COPY frontend/llm_toolkit_UI/package*.json ./

RUN npm install

CMD ["sh", "-c", "VITE_BACKEND_URI=$BACKEND_URI npm run dev -- --port $FRONTEND_PORT --host 0.0.0.0"]
