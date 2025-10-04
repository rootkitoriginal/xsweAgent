#!/bin/sh
set -e

# Copy the custom Prometheus configuration
cp /tmp/prometheus.yml /etc/prometheus/prometheus.yml

# Execute the original Prometheus entrypoint
exec /bin/prometheus --config.file=/etc/prometheus/prometheus.yml --storage.tsdb.path=/prometheus --web.console.libraries=/usr/share/prometheus/console_libraries --web.console.templates=/usr/share/prometheus/consoles
