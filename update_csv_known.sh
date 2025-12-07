#!/bin/bash

CSV_FILE="inbox/entity_updates.csv"

# Create file if not exists
if [ ! -f "$CSV_FILE" ]; then
    echo "entity_id,name,age,gender" > "$CSV_FILE"
fi

# Predefined entries
entries=(
    "Blake Blossom,30,Female"
    "Zuzanna Stamirowska,50,Female"
    "Keshav Manjhi,24,Male"
    "Adithya Ananth,20,Male"
    "Samay Raina,28,Male"
    "Greta Thunberg,22,Female"
    "Ashton Hill,25,Male"
    "Darren Jason Watkings Jr.,20,Male"
)

for person in "${entries[@]}"; do
    entity_id=$((RANDOM % 100000))
    echo "$entity_id,$person" >> "$CSV_FILE"
    sleep $((RANDOM % 11))
done
