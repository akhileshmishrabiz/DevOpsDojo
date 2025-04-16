# Build stage
FROM node:20-alpine as build

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies and the missing tailwind forms plugin
RUN npm install
RUN npm install @tailwindcss/forms

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built assets from build stage
COPY --from=build /app/build /usr/share/nginx/html

# Copy nginx configuration template and entrypoint script
COPY nginx.conf /etc/nginx/templates/default.conf.template
COPY docker-entrypoint.sh /docker-entrypoint.sh

# Install envsubst utility and make script executable
RUN apk add --no-cache bash && \
    chmod +x /docker-entrypoint.sh

# Expose port
EXPOSE 80

# Set default value for BACKEND_SERVICE_URL if not provided
ENV BACKEND_SERVICE_URL=http://backend:8000

# Start nginx with environment variable substitution
CMD ["/docker-entrypoint.sh"]