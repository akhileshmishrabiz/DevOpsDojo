#!/bin/bash

# Export environment variables so they're available to envsubst
export BACKEND_SERVICE_URL

# Replace environment variables in the Nginx config
envsubst '$BACKEND_SERVICE_URL' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

# Print the generated configuration for debugging
echo "Generated Nginx configuration:"
cat /etc/nginx/conf.d/default.conf

# Start Nginx
nginx -g "daemon off;"