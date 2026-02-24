FROM node:22-alpine AS frontend-builder

WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend /frontend
RUN npm run typecheck
RUN npm run build

FROM nginx:1.27-alpine

COPY ops/nginx/default.conf /etc/nginx/conf.d/default.conf
COPY --from=frontend-builder /frontend/dist /usr/share/nginx/html
