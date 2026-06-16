import os
import torch
import numpy as np
from flask import Flask, request, jsonify, render_template, send_from_directory, session
from flask_cors import CORS
import json
import csv
from model_drug_detection import ModelManager
from werkzeug.utils import secure_filename
from database import User, init_db

# Configuration
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'best_model.pth')

# Create Flask app
app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)
app.secret_key = 'your-secret-key-change-this-in-production'  # Change this in production!

# Cache control - prevent browser caching of HTML pages
@app.after_request
def set_cache_headers(response):
    """Add cache control headers to prevent caching"""
    if response.content_type and 'text/html' in response.content_type:
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

# Initialize database
init_db()

# Load model
model_manager = None
try:
    if os.path.exists(MODEL_PATH):
        model_manager = ModelManager(MODEL_PATH)
        print("[OK] Drug Detection Model loaded successfully")
    else:
        print(f"⚠ Model file not found at {MODEL_PATH}")
except Exception as e:
    print(f"⚠ Warning: Model loading error (app will still run): {e}")

@app.route('/')
def index():
    """Serve main page"""
    return render_template('index.html')

@app.route('/login')
def login():
    """Serve login page"""
    return render_template('login.html')

@app.route('/register')
def register():
    """Serve register page"""
    return render_template('register.html')

@app.route('/about')
def about():
    """Serve about page"""
    return render_template('about.html')

@app.route('/analysis')
def analysis():
    """Serve analysis page with model metrics"""
    return render_template('analysis.html')

@app.route('/drugs')
def drugs():
    """Serve drugs search page"""
    return render_template('drugs.html')

# ============================================
# AUTHENTICATION API ENDPOINTS
# ============================================

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    """Register a new user"""
    try:
        data = request.json
        
        if not data or not data.get('username') or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Create user
        success, message = User.create_user(
            data['username'],
            data['email'],
            data['password']
        )
        
        if success:
            return jsonify({'success': True, 'message': message}), 201
        else:
            return jsonify({'error': message}), 400
    
    except Exception as e:
        return jsonify({'error': f'Registration error: {str(e)}'}), 500


@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """Login a user"""
    try:
        data = request.json
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Missing username or password'}), 400
        
        # Authenticate user
        success, result = User.authenticate(data['username'], data['password'])
        
        if success:
            # Set session
            session['user_id'] = result['id']
            session['username'] = result['username']
            
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'user': result
            }), 200
        else:
            return jsonify({'error': result}), 401
    
    except Exception as e:
        return jsonify({'error': f'Login error: {str(e)}'}), 500


@app.route('/api/auth/logout', methods=['POST'])
def api_logout():
    """Logout a user"""
    try:
        session.clear()
        return jsonify({'success': True, 'message': 'Logged out successfully'}), 200
    except Exception as e:
        return jsonify({'error': f'Logout error: {str(e)}'}), 500


@app.route('/api/auth/user', methods=['GET'])
def api_get_user():
    """Get current user info"""
    try:
        if 'user_id' in session:
            user = User.get_user_by_id(session['user_id'])
            if user:
                return jsonify({'user': user}), 200
        
        return jsonify({'error': 'Not authenticated'}), 401
    
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500


@app.route('/api/auth/check', methods=['GET'])
def api_check_auth():
    """Check if user is authenticated"""
    try:
        if 'user_id' in session:
            return jsonify({'authenticated': True, 'username': session.get('username')}), 200
        else:
            return jsonify({'authenticated': False}), 200
    
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': model_manager is not None,
        'device': str(model_manager.device) if model_manager else 'N/A'
    })

@app.route('/api/predict', methods=['POST'])
def predict():
    """Predict from drug pair vector data (concatenated 4096 or 2097 dimensions)"""
    try:
        if not model_manager:
            return jsonify({'error': 'Model not loaded'}), 500
        
        data = request.json
        if not data or 'matrix' not in data:
            return jsonify({'error': 'No matrix data provided'}), 400
        
        # Convert to tensor
        matrix_data = np.array(data['matrix'], dtype=np.float32)
        
        # Ensure 2D: (batch_size, features) or (features,) -> (1, features)
        if matrix_data.ndim == 1:
            matrix_data = matrix_data.reshape(1, -1)
        
        # Validate feature size (should be 4096 for two 2048-dim vectors, or 2097 trimmed)
        features = matrix_data.shape[-1]
        if features not in [2097, 4096]:
            return jsonify({
                'error': f'Invalid feature size: {features}. Expected 2097 (trimmed) or 4096 (two 2048-dim vectors)'
            }), 400
        
        input_tensor = torch.from_numpy(matrix_data)
        
        # Run prediction (ModelManager.predict handles trimming from 4096 to 2097)
        result = model_manager.predict(input_tensor)
        
        return jsonify({
            'success': True,
            'prediction': result['prediction'],
            'class_name': result['class_name'],
            'confidence': round(float(result['confidence']) * 100, 2),
            'all_probabilities': result['probabilities'],
            'class_names': result['class_names'],
            'input_shape': list(matrix_data.shape),
            'interaction': 'Harmful' if result['prediction'] == 1 else 'Safe'
        })
    
    except Exception as e:
        return jsonify({'error': f'Prediction error: {str(e)}'}), 500


@app.route('/api/predict-csv', methods=['POST'])
def predict_csv():
    """Predict from CSV file upload"""
    try:
        if not model_manager:
            return jsonify({'error': 'Model not loaded'}), 500
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        # Parse CSV
        import csv
        import io
        
        stream = io.TextIOWrapper(file.stream, encoding='utf-8')
        rows = list(csv.reader(stream))
        
        # Convert to matrix
        matrix_data = []
        for row in rows:
            try:
                row_data = [float(x) for x in row]
                matrix_data.append(row_data)
            except ValueError:
                pass  # Skip non-numeric rows
        
        if not matrix_data:
            return jsonify({'error': 'No valid numerical data in CSV'}), 400
        
        matrix_array = np.array(matrix_data, dtype=np.float32)
        if matrix_array.ndim == 1:
            matrix_array = matrix_array.reshape(1, -1)
        
        input_tensor = torch.from_numpy(matrix_array)
        
        # Get predictions for all rows
        results = []
        with torch.no_grad():
            for i in range(input_tensor.shape[0]):
                sample = input_tensor[i:i+1]
                result = model_manager.predict(sample)
                results.append({
                    'row': i,
                    'prediction': result['prediction'],
                    'class_name': result['class_name'],
                    'confidence': round(float(result['confidence']) * 100, 2)
                })
        
        return jsonify({
            'success': True,
            'total_samples': len(results),
            'results': results,
            'class_names': model_manager.class_names
        })
    
    except Exception as e:
        return jsonify({'error': f'CSV prediction error: {str(e)}'}), 500

@app.route('/api/info', methods=['GET'])
def model_info():
    """Get model information"""
    return jsonify({
        'model': 'Drug-Drug Interaction Detector',
        'type': 'Binary Classification',
        'classes': {0: 'Safe', 1: 'Harmful'},
        'class_names': ['Safe', 'Harmful'],
        'input_size': 2097,
        'max_input_size': 4096,
        'input_description': 'Two 2048-dimensional molecular fingerprint vectors concatenated (4096 total, trimmed to 2097 for processing)',
        'framework': 'PyTorch',
        'task': 'Drug-Drug Interaction Detection',
        'example_input': {
            'drug1_name': 'Phenoxypropazine',
            'drug1_vector_length': 2048,
            'drug2_name': 'Synephrine',
            'drug2_vector_length': 2048,
            'combined_length': 4096,
            'processed_length': 2097
        }
    })

@app.route('/api/predict-sample', methods=['POST'])
def predict_sample():
    """Predict for a sample (combined drug vectors)
    
    Expects: {
        'drug1_vector': [...2048 values...],
        'drug2_vector': [...2048 values...]
    }
    
    Returns interaction prediction: 0=Safe, 1=Harmful
    """
    try:
        if not model_manager:
            return jsonify({'error': 'Model not loaded'}), 500
        
        data = request.json
        if not data or 'drug1_vector' not in data or 'drug2_vector' not in data:
            return jsonify({'error': 'Missing drug vectors'}), 400
        
        # Get vectors
        drug1_vector = np.array(data['drug1_vector'], dtype=np.float32)
        drug2_vector = np.array(data['drug2_vector'], dtype=np.float32)
        
        # Validate vector lengths
        if drug1_vector.shape[0] != 2048:
            return jsonify({'error': f'Drug 1 vector must be 2048 dimensions, got {drug1_vector.shape[0]}'}), 400
        if drug2_vector.shape[0] != 2048:
            return jsonify({'error': f'Drug 2 vector must be 2048 dimensions, got {drug2_vector.shape[0]}'}), 400
        
        # Concatenate both vectors (4096 total)
        combined_vector = np.concatenate([drug1_vector, drug2_vector])
        
        # Create tensor and run prediction
        # ModelManager.predict will handle trimming from 4096 to 2097
        input_tensor = torch.from_numpy(combined_vector.reshape(1, -1))
        result = model_manager.predict(input_tensor)
        
        return jsonify({
            'success': True,
            'prediction': result['prediction'],
            'class_name': result['class_name'],
            'confidence': round(float(result['confidence']) * 100, 2),
            'all_probabilities': result['probabilities'],
            'class_names': result['class_names'],
            'interaction_type': 'Harmful' if result['prediction'] == 1 else 'Safe',
            'input_details': {
                'drug1_vector_length': drug1_vector.shape[0],
                'drug2_vector_length': drug2_vector.shape[0],
                'combined_length': combined_vector.shape[0],
                'processed_length': 2097
            }
        })
    
    except Exception as e:
        return jsonify({'error': f'Prediction error: {str(e)}'}), 500

# ============================================
# DRUGS API ENDPOINTS
# ============================================

@app.route('/api/drugs/search', methods=['GET'])
def search_drugs():
    """Search drugs by name"""
    try:
        query = request.args.get('q', '').lower()
        filter_type = request.args.get('filter', 'all')
        
        if len(query) < 2:
            return jsonify({'success': False, 'error': 'Query too short'}), 400
        
        drugs = load_drugs_database()
        
        # Filter drugs based on search query
        results = [d for d in drugs if query in d['name'].lower()]
        
        # Apply type filter
        if filter_type != 'all':
            results = [d for d in results if d.get('type', '').lower() == filter_type.lower()]
        
        # Return results with fingerprints
        suggestions = results[:10]  # Return top 10 matches
        
        for drug in suggestions:
            # Include first 20 fingerprint values
            if 'fingerprint' in drug:
                drug['fingerprint'] = drug['fingerprint'][:20] if len(drug['fingerprint']) > 20 else drug['fingerprint']
        
        return jsonify({
            'success': True,
            'suggestions': suggestions,
            'total': len(results)
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/drugs/details', methods=['GET'])
def get_drug_details():
    """Get detailed information about a drug"""
    try:
        drug_name = request.args.get('name', '')
        
        if not drug_name:
            return jsonify({'success': False, 'error': 'Drug name required'}), 400
        
        drugs = load_drugs_database()
        
        # Find drug by name
        drug = next((d for d in drugs if d['name'].lower() == drug_name.lower()), None)
        
        if not drug:
            return jsonify({'success': False, 'error': 'Drug not found'}), 404
        
        # Return full fingerprint
        if 'fingerprint' not in drug:
            drug['fingerprint'] = [0.0] * 2048
        
        return jsonify({
            'success': True,
            'drug': drug
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def load_drugs_database():
    """Load drugs from CSV file"""
    drugs = []
    ddi_file = os.path.join(os.path.dirname(__file__), 'samples', 'ddi_pairs_with_smiles.csv')
    
    try:
        if os.path.exists(ddi_file):
            with open(ddi_file, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f)
                drug_names = set()
                
                for row in reader:
                    # Extract drug names from DDI pairs
                    if 'drug1' in row and row['drug1'] and row['drug1'] not in drug_names:
                        drug_names.add(row['drug1'])
                        drugs.append({
                            'name': row['drug1'],
                            'smiles': row.get('smiles1', ''),
                            'type': 'Drug',
                            'fingerprint': [0.0] * 2048  # Placeholder
                        })
                    
                    if 'drug2' in row and row['drug2'] and row['drug2'] not in drug_names:
                        drug_names.add(row['drug2'])
                        drugs.append({
                            'name': row['drug2'],
                            'smiles': row.get('smiles2', ''),
                            'type': 'Drug',
                            'fingerprint': [0.0] * 2048  # Placeholder
                        })
    except Exception as e:
        # If DDI file fails, try drug fingerprints file
        try:
            fp_file = os.path.join(os.path.dirname(__file__), 'samples', 'drug_fingerprints (1).csv')
            if os.path.exists(fp_file):
                with open(fp_file, 'r', encoding='utf-8', errors='ignore') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if 'drug_name' in row:
                            # Try to parse fingerprint
                            fingerprint = []
                            if 'fingerprint' in row:
                                try:
                                    fingerprint = [float(x) for x in str(row['fingerprint']).strip('[]').split(',')]
                                except:
                                    fingerprint = [0.0] * 2048
                            
                            drugs.append({
                                'name': row['drug_name'],
                                'smiles': row.get('smiles', ''),
                                'type': 'Drug',
                                'fingerprint': fingerprint[:2048] if fingerprint else [0.0] * 2048,
                                'features': len([x for x in fingerprint if x > 0]) if fingerprint else 0
                            })
        except:
            pass
    
    # If no drugs loaded, return sample data
    if not drugs:
        drugs = [
            {
                'name': 'Aspirin',
                'smiles': 'CC(=O)Oc1ccccc1C(=O)O',
                'type': 'Common',
                'fingerprint': [0.0] * 2048,
                'features': 150
            },
            {
                'name': 'Ibuprofen',
                'smiles': 'CC(C)Cc1ccc(cc1)C(C)C(=O)O',
                'type': 'Common',
                'fingerprint': [0.0] * 2048,
                'features': 180
            },
            {
                'name': 'Acetaminophen',
                'smiles': 'CC(=O)Nc1ccc(O)cc1',
                'type': 'Common',
                'fingerprint': [0.0] * 2048,
                'features': 120
            }
        ]
    
    return drugs

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print("Starting Flask server...")
    print(f"Model path: {MODEL_PATH}")
    app.run(debug=True, host='0.0.0.0', port=5000)
