# Example written based on the official
# Confluent Kakfa Get started guide https://github.com/confluentinc/examples/blob/7.1.1-post/clients/cloud/python/consumer.py

from confluent_kafka import Consumer
import json
import ccloud_lib
import time
import mlflow
import sklearn
import pandas as pd
from datetime import datetime, timezone

# Initialize configurations from "python.config" file
CONF = ccloud_lib.read_ccloud_config("python.config")
TOPIC_TRANS = "topic_trans"
TOPIC_PREDICT = "topic_predict"

# URL MLFlow
k_MLflow_Tracking_URL = "https://fraud-202406-70e02a9739f2.herokuapp.com/"
k_Logged_Model = "runs:/1fcd6f0ced3b491fa67f67f4d16f8712/model"
mlflow.set_tracking_uri(k_MLflow_Tracking_URL)
loaded_model = mlflow.sklearn.load_model(k_Logged_Model)

# Create Consumer instance
# 'auto.offset.reset=earliest' to start reading from the beginning of the
# topic if no committed offsets exist
consumer_conf = ccloud_lib.pop_schema_registry_params_from_config(CONF)
consumer_conf['group.id'] = 'trans_consumer'
consumer_conf['auto.offset.reset'] = 'earliest' # This means that you will consume latest messages that your script haven't consumed yet!
consumer = Consumer(consumer_conf)

# Subscribe to transaction topic
consumer.subscribe([TOPIC_TRANS])

# Process messages
try:
    while True:
        msg = consumer.poll(1.0) # Search for all non-consumed events. It times out after 1 second
        if msg is None:
            # No message available within timeout.
            # Initial message consumption may take up to
            # `session.timeout.ms` for the consumer group to
            # rebalance and start consuming
            print("Waiting for message or event/error in poll()")
            continue
        elif msg.error():
            print('error: {}'.format(msg.error()))
        else:
            # Check for Kafka message
            record_key = msg.key()
            record_value = msg.value()
            data = json.loads(record_value)
   
            columns = data['data']["columns"]
            index = data['data']["index"]
            rows = data['data']["data"]

            # Convertir le dictionnaire en DataFrame
            df = pd.DataFrame(rows, columns=columns)

            # ! DANGER - 17 is hard coded
            col = df["current_time"]
            df.insert(17, "unix_time", col)

            # convert to date string
            df.rename(columns={"current_time": "trans_date_trans_time"}, inplace=True)
            timestamp = df["trans_date_trans_time"].iloc[0]
            date = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
            str_date = date.strftime("%Y-%m-%d %H:%M:%S")

            df["trans_date_trans_time"] = df["trans_date_trans_time"].astype(str)
            df.at[index[0], "trans_date_trans_time"] = str_date

            # reorder columns
            cols = df.columns.tolist()
            reordered_cols = [cols[-1]] + cols[:-1]
            df = df[reordered_cols]

            # Ne garde que les colonnes attendues pour faire tourner le modèle (vire aussi la colonne is_fraud)
            model_columns = loaded_model.feature_names_in_ if hasattr(loaded_model, "feature_names_in_") else []
            prediction = loaded_model.predict(df[model_columns])
            print("Prediction : ", prediction)
            
            # Add new column 'prediction'
            df['prediction'] = prediction

            # TODO : write data into TOPIC_PREDICT 
           # producer.produce

except KeyboardInterrupt:
    pass
finally:
    # Leave group and commit final offsets
    consumer.close()