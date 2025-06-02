# JudiciAIre - Moroccan Legal AI Assistant 🏛️⚖️

JudiciAIre is an AI-powered legal assistant specialized in Moroccan law, particularly family law (Mudawana). The system provides accurate, clear, and helpful legal guidance based on Moroccan legal texts and regulations.

![JudiciAIre Demo](demo/1.jpg)

## 🌟 Features

- **Specialized Legal Knowledge**: Fine-tuned on Moroccan family law and legal procedures
- **Multilingual Support**: Handles queries in French and Arabic
- **User Authentication**: Secure user management with Clerk
- **Conversation History**: Save and manage legal consultations
- **Real-time Chat Interface**: Interactive legal assistance
- **Professional UI**: Clean and intuitive user interface

## 🏗️ Project Structure

```
JudiciAIre Project 1.2/
├── README.md                    # This file
├── Research_Paper.pdf           # Project documentation
├── demo/                        # UI Screenshots and demos
├── JudiciAIre Model/           # AI Model training and data
│   ├── judiciAIr_Fine_tunning.ipynb  # Model fine-tuning notebook
│   ├── all_qa.jsonl            # Training dataset
│   ├── code/                   # Legal documents (PDFs)
│   └── outputs/                # Processed data
└── judiciAIre UI/              # Full-stack web application
    ├── frontend/               # React + TypeScript frontend
    ├── backend/                # Flask Python backend
    └── package.json            # Root dependencies
```

## 🚀 Quick Start

### Prerequisites

- **Node.js** (v18 or higher)
- **Python** (v3.8 or higher)
- **MongoDB** (local or cloud instance)
- **Git**

### 1. Clone the Repository

```bash
git clone https://github.com/youssef-elkahlaoui/Judiciaire-Project-final-version-1.2.git
cd "Judiciaire Project 1.2"
```

### 2. Backend Setup (Flask API)

```bash
# Navigate to backend directory
cd "judiciAIre UI/backend"

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Environment Configuration

Create a `.env` file in the `backend` directory:

```env
# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017/judiciaire
# or for MongoDB Atlas:
# MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/judiciaire

# Clerk Authentication
CLERK_API_KEY=your_clerk_secret_key_here

# Hugging Face (if using hosted model)
HF_TOKEN=your_hf_token_here

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
```

#### Start Backend Server

```bash
# In the backend directory
python app.py
```

The backend will run on `http://localhost:5000`

### 3. Frontend Setup (React + TypeScript)

Open a new terminal window:

```bash
# Navigate to frontend directory
cd "judiciAIre UI/frontend"

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will run on `http://localhost:5173`

### 4. Access the Application

Open your browser and navigate to `http://localhost:5173`

## 📱 Demo Screenshots

### Landing Page
![Landing Page](demo/1.jpg)

### Model thinking
![Authentication](demo/2.jpg)

### Chat Interface
![Chat Interface](demo/3.jpg)

### Legal Consultation dark mode
![Legal Consultation](demo/4.jpg)

### Conversation History mobile version
![Conversation History](demo/5.jpg)

### Landing Page mobile version
![Additional Features](demo/1_2.jpg)

## 🔧 Configuration

### Database Setup

1. **MongoDB Local Installation**:
   - Install MongoDB Community Edition
   - Start MongoDB service
   - The application will automatically create the required database

2. **MongoDB Atlas (Cloud)**:
   - Create a MongoDB Atlas account
   - Create a new cluster
   - Get the connection string and update the `.env` file

### Authentication Setup (Clerk)

1. Create a [Clerk](https://clerk.com) account
2. Create a new application
3. Get your API keys from the Clerk dashboard
4. Update the `.env` file with your Clerk credentials

### AI Model Configuration

The application uses a fine-tuned language model. You can either:

1. **Use the pre-trained model** (recommended for quick setup)
2. **Train your own model** using the Jupyter notebook in `JudiciAIre Model/`

## 📖 API Documentation

### Main Endpoints

- `GET /` - Health check
- `POST /chat` - Send message to AI assistant
- `GET /conversations` - Get user conversations
- `POST /conversations` - Create new conversation
- `DELETE /conversations/<id>` - Delete conversation

### Example API Usage

```javascript
// Send a legal question
const response = await fetch('http://localhost:5000/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${userToken}`
  },
  body: JSON.stringify({
    message: "Quels sont les droits de la femme en cas de divorce au Maroc?",
    conversation_id: "conversation-uuid"
  })
});
```

## 🛠️ Development

### Frontend Development

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

### Backend Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python app.py

# Run with debug mode
FLASK_DEBUG=True python app.py
```

### Model Training

To retrain or fine-tune the model:

1. Navigate to `JudiciAIre Model/`
2. Open `judiciAIr_Fine_tunning.ipynb` in Jupyter Notebook or Google Colab
3. Follow the notebook instructions
4. Update the model path in the backend configuration

## 🔒 Security Features

- **JWT Authentication** via Clerk
- **CORS Protection** configured for development and production
- **Input Validation** for all API endpoints
- **Secret Management** via environment variables
- **No hardcoded credentials** in the codebase

## 📦 Deployment

### Frontend Deployment (Vercel/Netlify)

```bash
# Build the frontend
npm run build

# Deploy the dist/ folder to your hosting platform
```



## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 👨‍💻 Authors

- **Youssef Elkahlaoui** - *Initial work* - [GitHub Profile](https://github.com/youssef-elkahlaoui)
- **Anass Essafi** - *Initial work* - [GitHub Profile](https://github.com)
- **Ayoub Gorry** - *Initial work* - [GitHub Profile](https://github.com)

## 🙏 Acknowledgments

- Moroccan Ministry of Justice for legal document access
- Unsloth for efficient model fine-tuning
- Hugging Face for model hosting and transformers library
- Clerk for authentication services
- The open-source community for various tools and libraries


## 🔄 Changelog

### v1.2 (Current)
- ✅ Implemented user authentication with Clerk
- ✅ Added conversation history management
- ✅ Improved UI/UX with modern design
- ✅ Enhanced model performance
- ✅ Enhanced security measures
- ✅ Added comprehensive documentation

### v1.1
- ✅ Fine-tuned AI model on Moroccan legal texts
- ✅ Implemented basic chat functionality
- ✅ Created React frontend

### v1.0
- ✅ Initial project setup
- ✅ Data collection and preprocessing
- ✅ Basic model training

