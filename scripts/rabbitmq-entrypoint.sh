#!/bin/bash

set -e

# source common logging function
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
. "${SCRIPT_DIR}/common.sh"

if [ -z "$RABBITMQ_USER" ] || [ -z "$RABBITMQ_PASSWORD_HASH" ]; then
    log_msg "ERROR" "rabbitmq_init" "check" "1" "RABBITMQ_USER or RABBITMQ_PASSWORD_HASH is not set!"
    exit 1
fi

export RABBITMQ_DEFAULT_USER=""
export RABBITMQ_DEFAULT_PASS=""


cat > /etc/rabbitmq/definitions.json << EOF
{
    "users": [
        {
          "name": "$RABBITMQ_USER",
          "password_hash": "$RABBITMQ_PASSWORD_HASH",
          "hashing_algorithm": "rabbit_password_hashing_sha256",
          "tags": [
            "administrator"
          ],
          "limits": {}
        }
      ],
      "vhosts": [
        {
          "name": "/"
        }
      ],
      "permissions": [
        {
          "user": "$RABBITMQ_USER",
          "vhost": "/",
          "configure": ".*",
          "write": ".*",
          "read": ".*"
        }
      ],

    "queues": [
        {
            "name": "${RABBITMQ_PAYMENTS_NEW_QUEUE:-payments.new}",
            "vhost": "/",
            "durable": true,
            "auto_delete": false,
            "arguments": {
                "x-queue-type": "classic"
            }
        },
        {
            "name": "${RABBITMQ_PAYMENTS_NEW_DLQ_QUEUE:-payments.new.dlq}",
            "vhost": "/",
            "durable": true,
            "auto_delete": false,
            "arguments": {
                "x-queue-type": "classic"
            }
        }
    ],

    "exchanges": [],
    "bindings": []
}
EOF


export RABBITMQ_DEFINITIONS_FILE=/etc/rabbitmq/definitions.json


if [ "${NODE_ENV:-development}" = "development" ]; then
    log_msg "INFO" "rabbitmq_init" "config" "1" "create RabbitMQ configuration file for development..."
    cat > /etc/rabbitmq/rabbitmq.conf << EOF

management.load_definitions = /etc/rabbitmq/definitions.json
EOF
else
    log_msg "INFO" "rabbitmq_init" "config" "1" "RabbitMQ configuration file is provided via ConfigMap, skip creation..."
fi

log_msg "INFO" "rabbitmq_init" "complete" "2" "RabbitMQ initialization completed: user=$RABBITMQ_USER, definitions file=$RABBITMQ_DEFINITIONS_FILE"

exec docker-entrypoint.sh rabbitmq-server