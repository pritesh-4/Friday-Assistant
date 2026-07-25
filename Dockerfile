# Build Stage
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .
# We must pass Vite env vars at build time for the frontend
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}

RUN npm run build

# Production Stage (Nginx)
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
# Provide custom nginx config if necessary, else default is ok for basic SPA
# NOTE: To support React Router client-side routing, we override the default config:
RUN echo $'server {\n\
    listen 80;\n\
    location / {\n\
        root /usr/share/nginx/html;\n\
        index index.html index.htm;\n\
        try_files $uri $uri/ /index.html;\n\
    }\n\
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
