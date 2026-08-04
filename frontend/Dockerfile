# Stage 1: Build React SPA
FROM node:20-alpine AS build

WORKDIR /app

# Copy package descriptors and lockfiles
COPY package.json ./

# Install dependencies (frozen lockfile or clean dependencies)
RUN npm install

# Copy application source code
COPY . .

# Compile TypeScript and build production distribution bundle
RUN npm run build

# Stage 2: Serve using Nginx
FROM nginx:stable-alpine

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy production static assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
