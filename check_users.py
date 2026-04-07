from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['biological_age_predictor']

users = db.users.find()
print("Existing users in database:")
for user in users:
    print(f"  - Username: {user['username']}, Email: {user['email']}")

print(f"\nTotal: {db.users.count_documents({})} users")