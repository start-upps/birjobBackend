# =============================================================================
# BirJob Mobile Backend - Multi-stage Docker Build
# =============================================================================

# =============================================================================
# Stage 1: Base Dependencies
# =============================================================================
FROM node:18-alpine AS base

# Install system dependencies required for native modules
RUN apk add --no-cache \
    python3 \
    make \
    g++ \
    cairo-dev \
    jpeg-dev \
    pango-dev \
    musl-dev \
    giflib-dev \
    pixman-dev \
    pangomm-dev \
    libjpeg-turbo-dev \
    freetype-dev

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./
COPY prisma ./prisma/

# =============================================================================
# Stage 2: Dependencies Installation
# =============================================================================
FROM base AS dependencies

# Install all dependencies (including dev dependencies for build)
RUN npm ci --include=dev

# Generate Prisma client
RUN npx prisma generate

# =============================================================================
# Stage 3: Production Dependencies
# =============================================================================
FROM base AS production-deps

# Install only production dependencies
RUN npm ci --only=production --ignore-scripts

# Generate Prisma client for production
RUN npx prisma generate

# =============================================================================
# Stage 4: Build Stage (if needed for TypeScript or other build steps)
# =============================================================================
FROM dependencies AS build

# Copy source code
COPY . .

# Run any build steps (uncomment if you add TypeScript or build process)
# RUN npm run build

# =============================================================================
# Stage 5: Runtime
# =============================================================================
FROM node:18-alpine AS runtime

# Install runtime dependencies only
RUN apk add --no-cache \
    dumb-init \
    curl \
    tzdata

# Create app user for security
RUN addgroup -g 1001 -S nodejs
RUN adduser -S birjob -u 1001

# Set working directory
WORKDIR /app

# Copy production dependencies
COPY --from=production-deps /app/node_modules ./node_modules
COPY --from=production-deps /app/package*.json ./

# Copy Prisma files
COPY --chown=birjob:nodejs prisma ./prisma/

# Copy application code
COPY --chown=birjob:nodejs . .

# Create logs directory
RUN mkdir -p logs && chown birjob:nodejs logs

# Set proper permissions
RUN chown -R birjob:nodejs /app

# Switch to non-root user
USER birjob

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/api/health || exit 1

# Use dumb-init to handle signals properly
ENTRYPOINT ["dumb-init", "--"]

# Start the application
CMD ["npm", "start"]

# =============================================================================
# Stage 6: Development Environment
# =============================================================================
FROM dependencies AS development

# Install additional development tools
RUN npm install -g nodemon

# Copy all files
COPY . .

# Create logs directory
RUN mkdir -p logs

# Expose port and debugger port
EXPOSE 3000 9229

# Start with nodemon for development
CMD ["npm", "run", "dev"]

# =============================================================================
# Build Arguments and Labels
# =============================================================================
ARG BUILD_VERSION=latest
ARG BUILD_DATE
ARG VCS_REF

LABEL maintainer="BirJob Team <dev@birjob.az>"
LABEL version="${BUILD_VERSION}"
LABEL description="BirJob Mobile Backend API"
LABEL build-date="${BUILD_DATE}"
LABEL vcs-ref="${VCS_REF}"
LABEL org.opencontainers.image.title="BirJob Mobile Backend"
LABEL org.opencontainers.image.description="Node.js backend API for BirJob mobile applications"
LABEL org.opencontainers.image.version="${BUILD_VERSION}"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.source="https://github.com/Ismat-Samadov/birjobBackend"
LABEL org.opencontainers.image.licenses="MIT"

# =============================================================================
# Multi-platform support
# =============================================================================
# This Dockerfile supports building for multiple architectures:
# docker buildx build --platform linux/amd64,linux/arm64 -t birjob-backend .

# =============================================================================
# Usage Examples:
# =============================================================================
# 
# Development:
# docker build --target development -t birjob-backend:dev .
# docker run -p 3000:3000 -v $(pwd):/app birjob-backend:dev
#
# Production:
# docker build --target runtime -t birjob-backend:prod .
# docker run -p 3000:3000 birjob-backend:prod
#
# With build args:
# docker build --build-arg BUILD_VERSION=1.0.0 --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') -t birjob-backend .
# =============================================================================
