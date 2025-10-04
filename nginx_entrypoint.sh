#!/bin/sh
set -e

# Copy the custom Nginx configuration
cp /tmp/nginx.conf /etc/nginx/nginx.conf

# Execute the original Nginx command
exec nginx -g 'daemon off;'
