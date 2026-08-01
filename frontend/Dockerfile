# Use Node 22 slim image
FROM node:22-slim

WORKDIR /app

# Install pnpm
RUN npm install -g pnpm

# Set pnpm configuration for allowed builds
ENV pnpm_config_allow_builds='{"@sentry/cli":true,"core-js":true,"protobufjs":true,"unrs-resolver":true}'

# Copy package files and lockfile first for better layer caching
COPY package.json pnpm-lock.yaml .npmrc ./

# Install dependencies at build time with frozen lockfile for reproducibility
RUN pnpm install --frozen-lockfile

# Copy the rest of the application
COPY . .

# Expose the port Next.js runs on
EXPOSE 3000

CMD ["pnpm", "run", "dev"]
