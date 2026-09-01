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

EXPOSE 80
