
import os
import json
import uuid
import logging
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure, DuplicateKeyError
import requests
import jwt
from clerk_backend_api import Clerk
import torch
from transformers import AutoTokenizer, TextStreamer, StoppingCriteria, StoppingCriteriaList
from unsloth import FastLanguageModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"], supports_credentials=True)

# Clerk setup
clerk_api_key = os.getenv("CLERK_API_KEY")
clerk_jwt_key = os.getenv("JWKS_Public_Key")
model_name = os.getenv("HUGGINGFACE_MODEL_REPO_ID", "youssefELK/judiciaireModwanaLa")
api_key = os.getenv("HUGGINGFACE_API_KEY")
hf_space_url = os.getenv("HF_SPACE_URL")

if not clerk_api_key:
    raise ValueError("CLERK_API_KEY environment variable is not set")
if not api_key:
    raise ValueError("HUGGINGFACE_API_KEY environment variable is not set")

logger.info(f"🔍 Clerk API Key: {clerk_api_key[:10]}...")
logger.info(f"🔍 JWT Key: {clerk_jwt_key[:10] if clerk_jwt_key else 'Not set'}...")

# Initialize Clerk client
try:
    clerk_client = Clerk(clerk_api_key) if clerk_api_key else None
    logger.info("✅ Clerk client initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize Clerk client: {str(e)}")
    clerk_client = None

# MongoDB setup
try:
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000, retryWrites=True, retryReads=True)
    mongo_client.admin.command('ping')
    logger.info("✅ Connected to MongoDB successfully")
    
    db = mongo_client.get_database("chat_app_db")
    conversations_collection = db.conversations
    users_collection = db.users
    
    # Create indexes
    users_collection.create_index([("clerk_id", 1)], unique=True)
    users_collection.create_index([("email", 1)])
    conversations_collection.create_index([("user_id", 1)])
    conversations_collection.create_index([("conversation_id", 1)], unique=True)
    
except ConnectionFailure:
    logger.error("❌ Failed to connect to MongoDB. Please check if MongoDB is running.")
    raise
except Exception as e:
    logger.error(f"❌ MongoDB setup error: {str(e)}")
    raise

# Model loading
try:
    tokenizer = AutoTokenizer.from_pretrained("youssefELK/judiciaireModwanaLa")
    model, _ = FastLanguageModel.from_pretrained("youssefELK/judiciaireModwanaLa")
    model.eval()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)
    logger.info("✅ Model and tokenizer loaded successfully")
except Exception as e:
    logger.error(f"❌ Failed to load model or tokenizer: {str(e)}")
    raise

# Stopping criteria
class StopAfterSourceSentence(StoppingCriteria):
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer
        self.triggered = False

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        decoded = self.tokenizer.decode(input_ids[0], skip_special_tokens=True)
        if "Source:" in decoded and not self.triggered:
            source_index = decoded.find("Source:")
            after_source = decoded[source_index:]
            if any(p in after_source for p in [".", "؟", "!", "\n"]):
                self.triggered = True
                return True
        return False

# Inference function
def answer_question_stream(question: str) -> str:
    prompt = (
        "### Instruction :\n"
        "Vous êtes un assistant juridique de loi marocainne. Répondez à la question suivante de manière claire, concise, "
        "et uniquement en vous appuyant sur les textes de loi mentionnés.\n\n"
        f"### Question :\n{question}\n\n"
        "### Réponse :\n"
    )

    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    stopping_criteria = StoppingCriteriaList([StopAfterSourceSentence(tokenizer)])
    streamer = TextStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)

    generated = model.generate(
        **inputs,
        max_new_tokens=512,
        temperature=0.7,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id,
        streamer=streamer,
        stopping_criteria=stopping_criteria
    )

    output = tokenizer.decode(generated[0], skip_special_tokens=True)
    return output.split("### Réponse :")[-1].strip()

# Message standardization
def standardize_messages(messages):
    standardized = []
    for msg in messages:
        if "sender" in msg and "text" in msg and not ("role" in msg and "content" in msg):
            msg["role"] = "user" if msg["sender"] == "user" else "assistant"
            msg["content"] = msg["text"]
        standardized.append(msg)
    return standardized

# JWT verification
def verify_token(token, jwt_key):
    try:
        if jwt_key and isinstance(jwt_key, str) and jwt_key.startswith("{"):
            jwks = json.loads(jwt_key)
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")
            for key in jwks.get("keys", []):
                if key.get("kid") == kid:
                    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
                    break
            else:
                raise Exception("No matching JWKS key found for kid")
        else:
            public_key = jwt_key

        decoded = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            options={"verify_signature": True},
            leeway=10
        )
        logger.info(f"✅ Token verified successfully: {decoded.get('sub')}")
        return decoded
    except jwt.ExpiredSignatureError:
        raise Exception("Token has expired")
    except jwt.InvalidTokenError as e:
        raise Exception(f"Invalid token: {str(e)}")
    except Exception as e:
        raise Exception(f"JWT verification failed: {str(e)}")

# Authentication middleware
def require_auth(f):
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            logger.error("❌ Missing or invalid Authorization header")
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        token = auth_header.split(" ")[1]
        try:
            claims = verify_token(token, clerk_jwt_key)
            user_id = claims["sub"]
            request.user_id = user_id
            
            try:
                existing_user = users_collection.find_one({"clerk_id": user_id})
                if not existing_user:
                    logger.info(f"🔍 User {user_id} not found, creating minimal record")
                    users_collection.insert_one({
                        "clerk_id": user_id,
                        "email": None,
                        "name": None,
                        "created_at": datetime.now(timezone.utc),
                        "last_active": datetime.now(timezone.utc)
                    })
                    logger.info(f"✅ Created minimal user record for {user_id}")
                else:
                    users_collection.update_one(
                        {"clerk_id": user_id},
                        {"$set": {"last_active": datetime.now(timezone.utc)}}
                    )
                    logger.info(f"✅ Updated last_active for user {user_id}")
            except DuplicateKeyError as e:
                logger.error(f"❌ Duplicate key error: {str(e)}")
                return jsonify({"error": "Duplicate user ID", "details": str(e)}), 500
            except Exception as e:
                logger.error(f"❌ User database operation failed: {str(e)}")
                return jsonify({"error": "Failed to process user data", "details": str(e)}), 500
                
        except Exception as e:
            logger.error(f"❌ Token verification failed: {str(e)}")
            return jsonify({"error": "Invalid or expired token", "details": str(e)}), 401

        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

@app.route('/api/save-user', methods=["POST"])
@require_auth
def save_user():
    try:
        user_data = request.get_json()
        if not user_data:
            logger.error("❌ Missing user data in request")
            return jsonify({"error": "Missing user data"}), 400
        
        clerk_id = user_data.get("clerkid")
        email = user_data.get("email")
        name = user_data.get("name")
        
        if not clerk_id:
            logger.error("❌ clerkid is required")
            return jsonify({"error": "clerkid is required"}), 400
        
        now = datetime.now(timezone.utc)
        
        result = users_collection.update_one(
            {"clerk_id": clerk_id},
            {
                "$set": {
                    "email": email,
                    "name": name,
                    "last_active": now,
                    "last_updated": now
                },
                "$setOnInsert": {
                    "created_at": now
                }
            },
            upsert=True
        )
        
        if result.upserted_id:
            logger.info(f"✅ User {clerk_id} created successfully")
            return jsonify({"message": "User created successfully", "user_id": clerk_id}), 201
        else:
            logger.info(f"✅ User {clerk_id} updated successfully")
            return jsonify({"message": "User updated successfully", "user_id": clerk_id}), 200
    
    except Exception as e:
        logger.error(f"❌ User database operation failed: {str(e)}")
        return jsonify({"error": "Failed to save user", "details": str(e)}), 500

def call_huggingface_chat_model(message):
    try:
        API_URL = "https://api-inference.huggingface.co/models/youssefELK/judiciaireModwanaLa"
        headers = {"Authorization": f"Bearer {api_key}"}
        payload = {
            "messages": [{"role": "user", "content": message}],
            "model": model_name
        }
        
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        response_data = response.json()
        if "choices" not in response_data or not response_data["choices"]:
            raise ValueError("Invalid response format from HuggingFace API")
        return response_data["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Request failed: {str(e)}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response content: {e.response.text}")
        raise

@app.route('/api/save-convo', methods=['POST'])
@require_auth
def save_conversation():
    try:
        data = request.get_json()
        if not data:
            logger.error("❌ Missing request data")
            return jsonify({"error": "Missing request data"}), 400

        user_id = request.user_id
        conversation_id = data.get("conversationId")
        
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            
        title = data.get("title", "Untitled Conversation")
        messages = standardize_messages(data.get("messages", []))

        if not isinstance(messages, list):
            logger.error("❌ Messages must be an array")
            return jsonify({"error": "Messages must be an array"}), 400

        update_doc = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "title": title,
            "messages": messages,
            "updated_at": datetime.now(timezone.utc)
        }

        result = conversations_collection.update_one(
            {"conversation_id": conversation_id, "user_id": user_id},
            {
                "$set": update_doc,
                "$setOnInsert": {"created_at": datetime.now(timezone.utc)}
            },
            upsert=True
        )

        if result.matched_count > 0:
            logger.info(f"✅ Updated conversation {conversation_id}")
        else:
            logger.info(f"✅ Created conversation {conversation_id}")

        return jsonify({"conversationId": conversation_id}), 200

    except DuplicateKeyError as e:
        logger.error(f"❌ Duplicate key error: {str(e)}")
        return jsonify({"error": "Conversation ID already exists", "details": str(e)}), 400
    except Exception as e:
        logger.error(f"❌ Error saving conversation: {str(e)}")
        return jsonify({"error": "Failed to save conversation", "details": str(e)}), 500

@app.route('/api/get-convos', methods=['GET'])
@require_auth
def get_conversations():
    try:
        user_id = request.user_id
        conversations = conversations_collection.find(
            {"user_id": user_id},
            {"_id": 0, "conversation_id": 1, "title": 1, "created_at": 1, "updated_at": 1}
        ).sort("updated_at", -1)
        
        conversation_list = []
        for conv in conversations:
            if "created_at" in conv:
                if isinstance(conv["created_at"], datetime):
                    conv["created_at"] = conv["created_at"].isoformat()
                else:
                    conv["created_at"] = str(conv["created_at"])
            if "updated_at" in conv:
                if isinstance(conv["updated_at"], datetime):
                    conv["updated_at"] = conv["updated_at"].isoformat()
                else:
                    conv["updated_at"] = str(conv["updated_at"])
            conversation_list.append(conv)
            
        return jsonify({"conversations": conversation_list}), 200
    except Exception as e:
        logger.error(f"❌ Error fetching conversations: {str(e)}")
        return jsonify({"error": "Failed to fetch conversations", "details": str(e)}), 500

@app.route('/api/conversations/<conversation_id>', methods=['GET'])
@require_auth
def get_conversation(conversation_id):
    try:
        user_id = request.user_id
        logger.info(f"🔍 Fetching conversation {conversation_id} for user {user_id}")
        
        conversation = conversations_collection.find_one(
            {"conversation_id": conversation_id, "user_id": user_id},
            {"_id": 0}
        )
        
        if not conversation:
            logger.error(f"❌ Conversation {conversation_id} not found")
            return jsonify({"error": "Conversation not found"}), 404
        
        if "created_at" in conversation and isinstance(conversation["created_at"], datetime):
            conversation["created_at"] = conversation["created_at"].isoformat()
        if "updated_at" in conversation and isinstance(conversation["updated_at"], datetime):
            conversation["updated_at"] = conversation["updated_at"].isoformat()
        
        if "messages" in conversation and isinstance(conversation["messages"], list):
            conversation["messages"] = standardize_messages(conversation["messages"])
            logger.info(f"✅ Standardized {len(conversation['messages'])} messages")
        
        logger.info(f"✅ Returning conversation with {len(conversation.get('messages', []))} messages")
        return jsonify(conversation), 200
    except Exception as e:
        logger.error(f"❌ Error fetching conversation: {str(e)}")
        return jsonify({"error": "Failed to fetch conversation", "details": str(e)}), 500

@app.route('/api/get-convo/<conversation_id>', methods=['GET'])
@require_auth
def get_convo(conversation_id):
    return get_conversation(conversation_id)

@app.route('/api/conversations/<conversation_id>', methods=['DELETE'])
@require_auth
def delete_conversation(conversation_id):
    try:
        user_id = request.user_id
        result = conversations_collection.delete_one(
            {"conversation_id": conversation_id, "user_id": user_id}
        )
        
        if result.deleted_count == 0:
            logger.error(f"❌ Conversation {conversation_id} not found or already deleted")
            return jsonify({"error": "Conversation not found or already deleted"}), 404
            
        logger.info(f"✅ Conversation {conversation_id} deleted successfully")
        return jsonify({"message": "Conversation deleted successfully"}), 200
    except Exception as e:
        logger.error(f"❌ Error deleting conversation: {str(e)}")
        return jsonify({"error": "Failed to delete conversation", "details": str(e)}), 500

@app.route("/chat", methods=["POST"])
@require_auth
def chat():
    try:
        data = request.get_json()
        message = data.get("inputs")
        if not message:
            logger.error("❌ Missing input message")
            return jsonify({"error": "Missing input message"}), 400

        response_text = answer_question_stream(message)
        return jsonify({
            "response": response_text,
            "conversation_id": str(uuid.uuid4())
        })
    except Exception as e:
        logger.error(f"❌ Chat error: {str(e)}")
        return jsonify({"error": "Internal error", "details": str(e)}), 500

@app.route('/api/debug/conversation/<conversation_id>', methods=['GET'])
@require_auth
def debug_conversation(conversation_id):
    try:
        user_id = request.user_id
        conversation = conversations_collection.find_one(
            {"conversation_id": conversation_id, "user_id": user_id},
            {"_id": 0}
        )
        
        if not conversation:
            logger.error(f"❌ Conversation {conversation_id} not found")
            return jsonify({"error": "Conversation not found"}), 404
        
        debug_info = {
            "conversation_data": conversation,
            "message_count": len(conversation.get("messages", [])),
            "message_formats": []
        }
        
        for i, msg in enumerate(conversation.get("messages", [])):
            format_info = {
                "index": i,
                "has_role": "role" in msg,
                "has_content": "content" in msg,
                "has_sender": "sender" in msg,
                "has_text": "text" in msg,
                "format_type": "unknown"
            }
            
            if "role" in msg and "content" in msg:
                format_info["format_type"] = "role_content"
            elif "sender" in msg and "text" in msg:
                format_info["format_type"] = "sender_text"
            
            debug_info["message_formats"].append(format_info)
        
        return jsonify(debug_info), 200
    except Exception as e:
        logger.error(f"❌ Error in debug endpoint: {str(e)}")
        return jsonify({"error": "Debug operation failed", "details": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    try:
        mongo_client.admin.command('ping')
        clerk_status = "OK" if clerk_client else "Not initialized"
        
        return jsonify({
            "status": "healthy",
            "mongodb": "connected",
            "clerk": clerk_status,
            "api_version": "1.0.0"
        }), 200
    except Exception as e:
        logger.error(f"❌ Health check failed: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

@app.route('/test-clerk', methods=['GET'])
def test_clerk():
    try:
        if not clerk_client:
            logger.error("❌ Clerk client not initialized")
            return jsonify({"error": "Clerk client not initialized"}), 500
        users = clerk_client.users.list(limit=1)
        logger.info(f"✅ Clerk test successful: {len(users)} users fetched")
        return jsonify({"status": "success", "users": len(users)}), 200
    except Exception as e:
        logger.error(f"❌ Clerk test failed: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    os.environ["DEBUG"] = "1"
    app.run(debug=True)

