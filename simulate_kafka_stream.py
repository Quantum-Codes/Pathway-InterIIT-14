import pathway as pw


"""
2,Mehul Choksi,64,M
3,Rajinikanth,72,M
4,Prathamesh Deshpande,19,M
"""

# --- Configuration ---

# kafka topics
DB_TOPIC = 'db_updates'
MAIN_BACKEND_TOPIC = 'entities'
CSV_FILE_PATH = 'inbox/entity_updates.csv'  # <-- ADJUST THIS PATH

# --- Setup ---
# Must match the address exposed by your Docker container
rdkafka_settings = {
    "bootstrap.servers": "localhost:9092",
    "group.id": "0",
    "session.timeout.ms": "6000",
    "auto.offset.reset": "earliest",
}

class EntitiesSchema(pw.Schema):
    # IMPORTANT: no primary_key in streaming
    entity_id: str
    name: str
    age: str | None
    gender: str | None

entities = pw.io.csv.read(
    path=CSV_FILE_PATH,
    schema=EntitiesSchema,
    mode="streaming",
)

# replace write debezuium stuff to kafka here
pw.io.kafka.write(entities, rdkafka_settings, topic_name=MAIN_BACKEND_TOPIC, format="json")
pw.run(monitoring_level=pw.MonitoringLevel.NONE)

