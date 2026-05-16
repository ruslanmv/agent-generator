# syntax=docker/dockerfile:1.7

# ─── Stage 1 · build ─────────────────────────────────────────────
FROM node:20-alpine AS build
WORKDIR /app

# Copy lockfile + manifest first so dependency installs cache cleanly.
COPY package*.json ./

# `npm ci` if a lockfile exists, otherwise fall back to `npm install`.
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

COPY . .

# Type-check + build to dist/.
RUN npm run build

# ─── Stage 2 · serve ─────────────────────────────────────────────
FROM nginx:1.27-alpine AS runtime

# Single-page app fallback so deep links (/generate, /marketplace, …)
# resolve to index.html instead of 404.
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Static bundle.
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
