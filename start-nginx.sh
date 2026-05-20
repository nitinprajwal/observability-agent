#!/bin/sh
# start-nginx.sh — resolve ${NITRONODE_APP_URL} in nginx config at container startup.
#
# envsubst expands ALL $VAR patterns and would corrupt nginx variables like
# $host, $remote_addr, $http_cookie etc. Using sed with the exact literal
# placeholder is the only safe approach.
#
# sed pattern: \${NITRONODE_APP_URL}  (shell: \\\$ → sed regex \$ → literal $)
# sed replace: ${NITRONODE_APP_URL}   (shell expands the env var value here)

set -e

RESOLVED=$(sed "s|\\\${NITRONODE_APP_URL}|${NITRONODE_APP_URL:-http://host.docker.internal:3000}|g" \
    /etc/nginx/sites-available/default)

printf '%s\n' "$RESOLVED" > /etc/nginx/sites-available/default

# Ensure the symlink exists that nginx's http{} include picks up
ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default

exec nginx -g 'daemon off;'
