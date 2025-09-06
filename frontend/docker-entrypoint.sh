#!/bin/bash

# Set default backend URL if not provided
# For Docker Compose: http://backend:8000
# For Kubernetes: http://backend.NAMESPACE.svc.cluster.local:8000
if [ -z "$BACKEND_URL" ]; then
    # Try to detect if we're in Kubernetes by checking for service environment variables
    if [ -n "$KUBERNETES_SERVICE_HOST" ]; then
        # In Kubernetes, use the service DNS
        # Extract namespace from hostname or use default
        NAMESPACE=${NAMESPACE:-3-tier-app-eks}
        BACKEND_URL="http://backend.${NAMESPACE}.svc.cluster.local:8000"
    else
        # In Docker Compose, use the service name
        BACKEND_URL="http://backend:8000"
    fi
fi

echo "Using backend URL: $BACKEND_URL"

# Replace environment variables in the Nginx config
envsubst '${BACKEND_URL}' < /etc/nginx/conf.d/nginx.conf.template > /etc/nginx/conf.d/default.conf

# Print the generated configuration for debugging
echo "Generated Nginx configuration:"
cat /etc/nginx/conf.d/default.conf

# Start Nginx
nginx -g "daemon off;"