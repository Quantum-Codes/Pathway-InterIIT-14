chmod +x ./debezium_setup/connector.sh
docker compose up -d
sleep 5
docker compose exec debezium ./debezium_setup/connector.sh # set up the connector
