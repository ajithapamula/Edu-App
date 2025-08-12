from pymongo import MongoClient
from urllib.parse import quote_plus

# Escape credentials
username = quote_plus("connectly")
password = quote_plus("LT@connect25")  # Escape '@'

# MongoDB connection string
mongo_uri = f"mongodb://{username}:{password}@192.168.48.201:27017/admin"

# Connect to MongoDB
client = MongoClient(mongo_uri)
db = client["ml_notes"]
collection = db["summaries"]

# Fetch the latest 6 documents sorted by insertion order (descending)
latest_documents = collection.find().sort("_id", -1).limit(6)

# Print summaries
for idx, doc in enumerate(latest_documents, start=1):
    print(f"--- Summary {idx} ---")
    print("Summary    :")
    print(doc.get("summary"))
    print()
