# Use Node 22 slim image
FROM node:22-slim

WORKDIR /app

# Install pnpm
RUN npm install -g pnpm
ENV PNPM_CONFIG_ONLY_ALLOW_TRUSTED_DEPENDENCIES=false

# Copy package files and lockfile
# We copy pnpm-lock.yaml if it exists to leverage caching
COPY package.json pnpm-lock.yaml* .npmrc ./

# Install dependencies
# We remove --ignore-scripts to allow trusted dependencies to build
# We use --no-frozen-lockfile to avoid issues with potential lockfile mismatches in the container
RUN pnpm install --no-frozen-lockfile

# Copy the rest of the application
COPY . .

# Expose the port Next.js runs on
EXPOSE 3000

CMD ["pnpm", "run", "dev"]
