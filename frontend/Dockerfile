# Build stage
FROM node:20-alpine as build

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install
RUN npm install @tailwindcss/forms

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install production dependencies only
RUN npm install express http-proxy-middleware

# Copy built assets from build stage
COPY --from=build /app/build ./build

# Copy server file
COPY server.js .

# Expose port
EXPOSE 80

# Set environment variable for backend URL
ENV BACKEND_URL=http://backend.3-tier-app-eks.svc.cluster.local:8000

# Start the server
CMD ["node", "server.js"]