#!/bin/bash

CSV_FILE="inbox/entity_updates.csv"

# Create file if not exists
if [ ! -f "$CSV_FILE" ]; then
    echo "entity_id,name,age,gender" > "$CSV_FILE"
fi

count=0
limit=5   # number of rows you want

while [ "$count" -lt "$limit" ]; do
    entity_id=$((RANDOM % 100000))
    name="User$((RANDOM % 9999))"
    age=$((RANDOM % 82 + 18))
    gender=$(shuf -n 1 <(printf "Male\nFemale\nOther"))

    echo "$entity_id,$name,$age,$gender" >> "$CSV_FILE"

    count=$((count + 1))

    sleep $((RANDOM % 11))
done