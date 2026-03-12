import psycopg2, time
import pathway as pw


connection_string_parts = {
    "host": "localhost",
    "port": "5432",
    "dbname": "values_db",
    "user": "user",
    "password": "password",
}

conn = psycopg2.connect(
    host=connection_string_parts["host"],
    port=connection_string_parts["port"],
    dbname=connection_string_parts["dbname"],
    user=connection_string_parts["user"],
    password=connection_string_parts["password"]
)
cursor = conn.cursor()

# function to get two numbers from database
def get_rps_scores(record_id):
    try:
        # Align with schema: Users(current_rps_not, current_rps_360)
        query = "SELECT current_rps_not, current_rps_360 FROM Users WHERE user_id = %s"
        cursor.execute(query, (record_id,))
        row = cursor.fetchone()

        if row:
            return row[0], row[1]
        return None, None

    except Exception as e:
        print(f"Database error (Read): {e}")
        return None, None

# Function to Update the Database
def update_rps_in_db(record_id, new_rps0_val):
    try:
        # Update current_rps_not to the new value
        query = "UPDATE Users SET current_rps_not = %s, last_rps_calculation = NOW() WHERE user_id = %s"
        
        # Execute and COMMIT the transaction
        cursor.execute(query, (new_rps0_val, record_id))
        conn.commit()
        
        print(f"SUCCESS: Updated User {record_id} | New current_rps_not: {new_rps0_val:.4f}")

    except Exception as e:
        print(f"Database error (Update): {e}")

def insert_toxicity_history(record_id, rps_not_val, rps_360_val, trigger="external_validation"):
    try:
        # Minimal insertion respecting table columns; other scores left NULL
        query = (
            "INSERT INTO ToxicityHistory (user_id, rps_not, rps_360, calculation_trigger, calculated_at, time, diff) "
            "VALUES (%s, %s, %s, %s, NOW(), %s, %s)"
        )
        ts_ms = int(time.time() * 1000)
        diff = 1
        cursor.execute(query, (record_id, rps_not_val, rps_360_val, trigger, ts_ms, diff))
        conn.commit()
        print(f"SUCCESS: Inserted ToxicityHistory for User {record_id} | rps_not={rps_not_val:.4f}, rps_360={rps_360_val:.4f}")
    except Exception as e:
        print(f"Database error (Insert ToxicityHistory): {e}")

# Calculation Logic
def new_rps_pred(x, y):
    # Probability Union Formula: P(A or B)
    return 1 - ((1 - x) * (1 - y))

#as soon as we get the validation match from external system

@pw.udf
def update_rps_based_on_conditions(id_to_search, rps360_new):
    # Fetch current values
    rps0, rps360 = get_rps_scores(id_to_search)

    if rps0 is not None and rps360 is not None:
        print(f"Current State: current_rps_not={rps0}, current_rps_360={rps360} | new_rps_360={rps360_new} for User ID: {id_to_search}")
        
        if rps0 <= 0.2:
            new_rps = rps360_new
        else:
            new_rps = new_rps_pred(rps0, rps360_new)
        update_rps_in_db(id_to_search, new_rps)
        insert_toxicity_history(id_to_search, new_rps, rps360_new, trigger="external_validation")
    
    return rps0
          