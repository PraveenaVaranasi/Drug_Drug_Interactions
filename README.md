# AI Model Predictor - Flask Integration

A modern, full-stack web application for ML model inference with a clean, responsive UI.

## 📋 Project Structure

```
Bhavani_project/
├── app.py                 # Flask application
├── model.py              # Model loading and inference
├── requirements.txt      # Python dependencies
├── best_model.pth        # PyTorch model file
├── templates/
│   └── index.html        # Main HTML template
├── static/
│   ├── css/
│   │   └── style.css     # Styling (10KB+ modern CSS)
│   └── js/
│       └── script.js     # Frontend logic
└── uploads/              # Uploaded files directory
```

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- pip package manager

### Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Run the Flask server:**
```bash
python app.py
```

3. **Access the application:**
- Open your browser and go to: `http://localhost:5000`

## 📦 Features

### Backend (Flask + PyTorch)
- ✅ **Model Loading**: Automatic PyTorch model checkpoint loading
- ✅ **REST API**: Multiple endpoints for predictions
  - `POST /api/predict` - Upload image files
  - `POST /api/predict-base64` - Send base64 encoded images
  - `GET /api/health` - Server status check
  - `GET /api/info` - Model information
- ✅ **Error Handling**: Comprehensive error messages and validation
- ✅ **CORS Support**: Cross-origin requests enabled
- ✅ **Device Detection**: Automatic GPU/CPU selection

### Frontend
- 🎨 **Modern UI**: Gradient backgrounds, smooth animations, clean design
- 📱 **Responsive Design**: Works on desktop, tablet, and mobile
- 🖼️ **Image Upload**: Drag-and-drop or file browser
- ✏️ **Drawing Canvas**: Draw directly on canvas
- 📊 **Results Display**: 
  - Large prediction number with confidence percentage
  - Confidence progress bar
  - Probability distribution chart (10 classes)
  - JSON details viewer
- ⚡ **Real-time Updates**: Instant visual feedback
- 🎯 **Status Indicators**: Server connection status

## 🛠️ API Documentation

### Health Check
```bash
GET /api/health
```
Response:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "device": "cuda"
}
```

### Model Info
```bash
GET /api/info
```
Response:
```json
{
  "model": "Image Classification Model",
  "classes": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
  "input_size": [1, 28, 28],
  "framework": "PyTorch"
}
```

### Predict (File Upload)
```bash
POST /api/predict
Content-Type: multipart/form-data

file: <image_file>
```
Response:
```json
{
  "success": true,
  "prediction": 3,
  "confidence": 94.52,
  "probabilities": [0.001, 0.002, ..., 0.9452],
  "image_preview": "data:image/png;base64,..."
}
```

### Predict (Base64)
```bash
POST /api/predict-base64
Content-Type: application/json

{
  "image": "data:image/png;base64,..."
}
```

## 🎨 UI Components

- **Header**: Branding with server status indicator
- **Upload Panel**: Drag-drop zone, file browser, drawing canvas
- **Results Panel**: Prediction display, confidence metrics, probability chart
- **Info Section**: Model details and framework information
- **Footer**: Copyright and attribution

## 🔧 Customization

### Model Architecture
Edit `model.py` to match your model's architecture:
```python
def _create_model(self, state_dict):
    # Customize your model architecture here
    model = nn.Sequential(...)
    return model.to(self.device)
```

### UI Styling
Modify `static/css/style.css` for custom colors and styling:
```css
:root {
    --primary-color: #6366f1;  /* Change primary color */
    --secondary-color: #8b5cf6;
    /* ... more colors ... */
}
```

### Input Size
Adjust image preprocessing in `model.py`:
```python
def preprocess_image(image, target_size=(28, 28)):
    # Change target_size to match your model's input
```

## 📱 Supported Image Formats
- PNG
- JPEG / JPG
- GIF
- BMP

## 🚢 Production Deployment

### Using Gunicorn
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Using Docker
```bash
docker build -t ai-predictor .
docker run -p 5000:5000 ai-predictor
```

## 🐛 Troubleshooting

### Model not loading
- Ensure `best_model.pth` is in the project root
- Check file path in `app.py`
- Verify PyTorch installation: `python -c "import torch; print(torch.__version__)"`

### Port already in use
```bash
# Change port in app.py
app.run(debug=True, host='0.0.0.0', port=5001)
```

### CORS errors
- CORS is already enabled in `app.py` with `CORS(app)`
- Ensure request headers are correct

## 📚 Technologies Used

- **Backend**: Flask 2.3.0, PyTorch 2.0.0
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Database**: N/A (Stateless API)
- **Deployment**: Gunicorn, Docker ready

## 📄 License

This project is provided as-is for educational purposes.

---

**Built with ❤️ for ML Model Inference**
