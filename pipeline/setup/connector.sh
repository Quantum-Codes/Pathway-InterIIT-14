#!/bin/bash


# "table.include.list" is a kafka topic
# check whats "database.history.kafka.topic"
while true; do
  http_code=$(curl -o /dev/null -w "%{http_code}" -H 'Content-Type: application/json' localhost:8083/connectors --data '{
    "name": "values-connector",
    "config": {
      "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
      "plugin.name": "pgoutput",
      "database.hostname": "postgres",
      "database.port": "5432",
      "database.user": "user",
      "database.password": "password",  
      "database.dbname" : "values_db",
      "topic.prefix": "postgres",
      "table.include.list": "public.ToxicityHistory,public.Transactions",
      "database.history.kafka.bootstrap.servers": "broker:29092",
      "database.history.kafka.topic": "schema-changes.inventory",
      "snapshot.mode": "initial"
    }
  }')
  if [ "$http_code" -eq 201 ]; then
    echo "Debezium connector has been created successfully"
    break
  # The 409 check is now redundant since we delete first, but keep the loop for robustness
  elif [ "$http_code" -eq 409 ]; then
    echo "Error 409: Conflict detected. Connector likely already exists."
    break
  else
    echo "Retrying Debezium connection creation in 1 second... $http_code"
    sleep 1
  fi
done