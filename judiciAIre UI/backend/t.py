from pymongo import MongoClient

# Connect to your MongoDB server
client = MongoClient("mongodb+srv://Anass:Anas..12..@moroccguide.j19ie.mongodb.net/?retryWrites=true&w=majority&appName=MoroccGuide")

# Access the database and collection
db = client["chat_app_db"]
conversations_collection = db["conversations"]

# Delete all documents in the collection
result = conversations_collection.delete_many({})

print(f"✅ Deleted {result.deleted_count} conversation(s).")
