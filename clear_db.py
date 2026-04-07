from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['biological_age_predictor']

# Delete all users
result = db.users.delete_many({})
print(f"✅ Deleted {result.deleted_count} users")

# Delete all predictions
result = db.predictions.delete_many({})
print(f"✅ Deleted {result.deleted_count} predictions")

print("\n📊 Database is now empty!")
print("You can now register new users.")