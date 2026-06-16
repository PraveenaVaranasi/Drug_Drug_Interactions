import torch
import torch.nn as nn
import numpy as np
import os

class DrugDetectionModel(nn.Module):
    """Drug Detection Model - expects numerical matrix inputs"""
    
    def __init__(self, input_size=2097):
        super(DrugDetectionModel, self).__init__()
        # Architecture for drug detection from spectroscopy/chemical data
        self.fc1 = nn.Linear(input_size, 512)
        self.bn1 = nn.BatchNorm1d(512)
        self.relu = nn.ReLU()
        self.dropout1 = nn.Dropout(0.3)
        
        self.fc2 = nn.Linear(512, 256)
        self.bn2 = nn.BatchNorm1d(256)
        self.dropout2 = nn.Dropout(0.3)
        
        self.fc3 = nn.Linear(256, 128)
        self.bn3 = nn.BatchNorm1d(128)
        self.dropout3 = nn.Dropout(0.2)
        
        self.fc4 = nn.Linear(128, 64)
        self.bn4 = nn.BatchNorm1d(64)
        
        # Binary classification: Drug / No Drug
        self.fc5 = nn.Linear(64, 2)
        self.softmax = nn.Softmax(dim=1)
    
    def forward(self, x):
        x = self.fc1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.dropout1(x)
        
        x = self.fc2(x)
        x = self.bn2(x)
        x = self.relu(x)
        x = self.dropout2(x)
        
        x = self.fc3(x)
        x = self.bn3(x)
        x = self.relu(x)
        x = self.dropout3(x)
        
        x = self.fc4(x)
        x = self.bn4(x)
        x = self.relu(x)
        
        x = self.fc5(x)
        return x


class ModelManager:
    """Manages drug detection model loading and inference"""
    
    def __init__(self, model_path):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = self._load_drug_detection_model(model_path)
        self.model.eval()
        self.class_names = ['Safe', 'Harmful']
        self.input_size = 2097
    
    def _load_drug_detection_model(self, model_path):
        """Load drug detection model from checkpoint"""
        try:
            # First, try to load from a standard .pth file if available
            # Check for best_model_trained.pth (newly trained model)
            if os.path.basename(model_path) == 'best_model.pth':
                trained_path = os.path.join(os.path.dirname(model_path), 'best_model_trained.pth')
                if os.path.exists(trained_path):
                    print(f"Found trained model at {trained_path}, loading...")
                    return self._load_from_file(trained_path)
            
            # Then try the provided path
            if os.path.isfile(model_path) and model_path.endswith('.pth'):
                return self._load_from_file(model_path)
            elif os.path.isdir(model_path):
                return self._load_from_distributed_checkpoint(model_path)
            else:
                raise FileNotFoundError(f"Model path not found: {model_path}")
        except Exception as e:
            print(f"Warning: {e}")
            # Return model with random initialization
            return DrugDetectionModel(2097).to(self.device)
    
    def _load_from_distributed_checkpoint(self, model_dir):
        """Load from distributed checkpoint format - manual reconstruction"""
        try:
            # Find the actual best_model directory
            if os.path.basename(model_dir) != 'best_model' and os.path.exists(os.path.join(model_dir, 'best_model')):
                model_dir = os.path.join(model_dir, 'best_model')
            
            # Check if the checkpoint directory structure exists
            data_dir = os.path.join(model_dir, 'data')
            if not os.path.exists(data_dir):
                raise ValueError(f"Data directory not found at {data_dir}")
            
            # Create model instance
            model = DrugDetectionModel(2097).to(self.device)
            
            # Load raw weight files and reconstruct state dict
            state_dict = {}
            try:
                # Expected layer sizes based on model architecture:
                # File 0: fc1.weight (512, 2097) = 1,073,664 floats (8.3MB)
                # File 1: fc1.bias (512) + bn1.weight (512) + bn1.bias (512) = 1536 floats
                # File 2: fc2.weight (256, 512) = 131,072 floats + bn2.weight/bias (512) = 131,584 floats
                # File 3: bn2 params (512) + more
                # etc...
                # This requires careful unpacking - try simpler approach first
                
                # Try to load from each data file
                print("Attempting to reconstruct state dict from raw weight files...")
                all_floats = []
                
                for i in range(10):
                    file_path = os.path.join(data_dir, str(i))
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as f:
                            data = np.frombuffer(f.read(), dtype=np.float32)
                            all_floats.extend(data)
                            print(f"  Loaded file {i}: {len(data)} floats")
                
                if all_floats:
                    print(f"Total floats loaded: {len(all_floats)}")
                    # Calculate expected parameter count
                    expected_params = sum(p.numel() for p in model.parameters())
                    print(f"Expected model parameters: {expected_params}")
                    
                    if len(all_floats) == expected_params:
                        # Reshape and assign weights to state dict
                        offset = 0
                        for name, param in model.named_parameters():
                            param_size = param.numel()
                            param_data = np.array(all_floats[offset:offset+param_size], dtype=np.float32)
                            state_dict[name] = torch.from_numpy(param_data.reshape(param.shape)).to(self.device)
                            offset += param_size
                        
                        model.load_state_dict(state_dict)
                        print("✓ Successfully reconstructed weights from distributed checkpoint files")
                        return model
                    else:
                        print(f"⚠ Weight count mismatch: got {len(all_floats)}, expected {expected_params}")
            
            except Exception as e:
                print(f"⚠ Error reconstructing from raw files: {e}")
            
            print("⚠ Could not load distributed checkpoint weights")
            return model
                
        except Exception as e:
            print(f"⚠ Error in distributed checkpoint loading: {e}")
            model = DrugDetectionModel(2097).to(self.device)
            return model
    
    def _load_from_distributed_checkpoint_manual(self, model_dir):
        """Fallback: manually load distributed checkpoint format"""
        try:
            # Find the actual best_model directory
            if os.path.basename(model_dir) != 'best_model' and os.path.exists(os.path.join(model_dir, 'best_model')):
                model_dir = os.path.join(model_dir, 'best_model')
            
            # Try loading via pickle if available
            import pickle
            data_pkl = os.path.join(model_dir, 'data.pkl')
            
            if os.path.exists(data_pkl):
                with open(data_pkl, 'rb') as f:
                    # Create a custom unpickler for handling persistent IDs
                    class CustomUnpickler(pickle.Unpickler):
                        def persistent_load(self, pid):
                            # Handle persistent IDs from torch DCP format
                            return pid
                    
                    data = CustomUnpickler(f).load()
                    if isinstance(data, dict) and 'state_dict' in data:
                        model = DrugDetectionModel(2097).to(self.device)
                        model.load_state_dict(data['state_dict'])
                        print("✓ Successfully loaded from pickle metadata")
                        return model
        except Exception as e:
            print(f"⚠ Manual loading failed: {e}")
        
        # Fallback to uninitialized model
        model = DrugDetectionModel(2097).to(self.device)
        print("⚠ Could not load weights, using random initialization")
        return model
    
    def _load_from_file(self, model_path):
        """Load from single .pth file"""
        try:
            checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)
            model = DrugDetectionModel(2097)
            if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
                model.load_state_dict(checkpoint['model_state_dict'])
            elif isinstance(checkpoint, dict):
                model.load_state_dict(checkpoint)
            model.to(self.device)
            return model
        except Exception as e:
            print(f"Error loading from file: {e}")
            return DrugDetectionModel(2097).to(self.device)
    
    def predict(self, input_tensor):
        """Run inference on drug pair vector input
        
        Args:
            input_tensor: torch.Tensor of shape (batch_size, features)
                         Features can be 4096 (2 drug vectors 2048 each) or 2097 (trimmed)
        
        Returns:
            dict with prediction results
        """
        with torch.no_grad():
            try:
                # Ensure input is on correct device
                input_tensor = input_tensor.to(self.device)
                
                # Handle input size: trim from 4096 to 2097 if needed
                if input_tensor.shape[-1] > self.input_size:
                    input_tensor = input_tensor[:, :self.input_size]
                    print(f"Input trimmed from {input_tensor.shape[-1] + (4096 - self.input_size)} to {self.input_size} features")
                elif input_tensor.shape[-1] < self.input_size:
                    # Pad with zeros if input is smaller than expected
                    padding = self.input_size - input_tensor.shape[-1]
                    input_tensor = torch.nn.functional.pad(input_tensor, (0, padding), value=0.0)
                    print(f"Input padded from {input_tensor.shape[-1] - padding} to {self.input_size} features")
                
                # Get model output
                output = self.model(input_tensor)
                probabilities = torch.softmax(output, dim=1)
                
                # Get prediction
                prediction = torch.argmax(probabilities, dim=1)
                confidence = torch.max(probabilities, dim=1)[0]
                
                return {
                    'prediction': int(prediction.item()),
                    'class_name': self.class_names[int(prediction.item())],
                    'confidence': float(confidence.item()),
                    'probabilities': probabilities[0].cpu().numpy().tolist(),
                    'class_names': self.class_names
                }
            except Exception as e:
                print(f"Prediction error: {e}")
                return {
                    'prediction': 0,
                    'class_name': self.class_names[0],
                    'confidence': 0.5,
                    'probabilities': [0.5, 0.5],
                    'class_names': self.class_names,
                    'error': str(e)
                }
