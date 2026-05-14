FROM node:22-slim

WORKDIR /app
COPY package.json ./
# Use npm install to avoid pnpm networking/timeout issues in Docker Desktop on Windows
RUN npm install

COPY . .

CMD ["npm", "run", "dev"]
