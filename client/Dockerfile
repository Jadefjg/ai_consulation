FROM node:22-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
ARG NPM_CONFIG_REGISTRY=https://registry.npmjs.org
ARG NODE_OPTIONS=--max-old-space-size=384
ENV NPM_CONFIG_REGISTRY=${NPM_CONFIG_REGISTRY} \
    NODE_OPTIONS=${NODE_OPTIONS}
RUN npm ci --no-audit --no-fund

COPY . .
RUN npm run build

FROM nginx:1.27-alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
RUN mkdir -p /usr/share/nginx/html-h5 \
    && printf '%s\n' '<!doctype html><meta charset="utf-8"><title>患者端 H5</title><p>请将 mobile H5 构建产物放到此目录</p>' \
    > /usr/share/nginx/html-h5/index.html

EXPOSE 80
