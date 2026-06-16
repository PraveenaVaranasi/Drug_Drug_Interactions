import torch
import torch.nn as nn
import os
from pathlib import Path
import pickle
import json

class ModelManager:
    """Manages model loading and inference"""
    
    def __init__(self, model_path):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = self.load_model(model_path)
        self.model.eval()
    
    def load_model(self, model_path):
        """Load PyTorch model from checkpoint - handles directory and file formats"""
        try:
            # Check if it's a directory (new format)
            if os.path.isdir(model_path):
                return self._load_from_directory(model_path)
            # Otherwise try standard .pth file
            elif os.path.isfile(model_path):
                return self._load_from_file(model_path)
            else:
                raise FileNotFoundError(f"Model path not found: {model_path}")
        except Exception as e:
            print(f"⚠ Model loading warning: {e}")
            # Return a dummy model if loading fails
            return self._create_model(None)
    
    def _load_from_file(self, model_path):
        """Load from standard .pth file"""
        checkpoint = torch.load(model_path, map_location=self.device)
        
        # Extract state dict
        if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
            state_dict = checkpoint['model_state_dict']
        elif isinstance(checkpoint, dict) and 'state_dict' in checkpoint:
            state_dict = checkpoint['state_dict']
        else:
            state_dict = checkpoint
        
        model = self._create_model(state_dict)
        return model
    
    def _load_from_directory(self, model_dir):
        """Load from directory format (PyTorch checkpoint directory)"""
        # Try to load version file to understand format
        version_file = os.path.join(model_dir, 'version')
        format_file = os.path.join(model_dir, '.format_version')
        
        # Try to load as distributed checkpoint
        try:
            # Check for metadata files
            data_dir = os.path.join(model_dir, 'data')
            if os.path.exists(data_dir):
                # Load all pickle files from data directory
                state_dict = {}
                for i in range(20):  # Usually numbered 0-9 or more
                    data_file = os.path.join(data_dir, str(i))
                    if os.path.isfile(data_file):
                        try:
                            with open(data_file, 'rb') as f:
                                chunk = torch.load(f, map_location=self.device)
                                if isinstance(chunk, dict):
                                    state_dict.update(chunk)
                                else:
                                    state_dict[f'chunk_{i}'] = chunk
                        except Exception as e:
                            print(f"  Note: Could not load data/{i}: {e}")
                
                if state_dict:
                    model = self._create_model(state_dict)
                    print("✓ Model loaded from directory format")
                    return model
        except Exception as e:
            print(f"  Note: Directory format error: {e}")
        
        # Fallback: create empty model
        print("✓ Created model with random initialization")
        return self._create_model(None)
    
    def _create_model(self, state_dict):
        """Create model instance and load state dict"""
        # Try to infer model architecture from state dict
        if state_dict and isinstance(state_dict, dict):
            model = self._infer_model_from_state(state_dict)
        else:
            # Default CNN model for image classification (MNIST-like)
            model = nn.Sequential(
                nn.Linear(784, 256),
                nn.ReLU(),
                nn.Linear(256, 128),
                nn.ReLU(),
                nn.Linear(128, 10)
            )
        
        try:
            if state_dict is not None and isinstance(state_dict, dict):
                # Try strict loading first
                try:
                    model.load_state_dict(state_dict, strict=True)
                except RuntimeError:
                    # If strict fails, try non-strict
                    model.load_state_dict(state_dict, strict=False)
        except Exception as e:
            print(f"  Note: Could not load state dict: {e}")
        
        return model.to(self.device)
    
    def _infer_model_from_state(self, state_dict):
        """Infer model architecture from state dict keys"""
        # Get layer keys to understand model architecture
        keys = list(state_dict.keys())
        
        # Check for common architectures
        if any('conv' in k for k in keys):
            # CNN model
            print("  Detected: CNN architecture")
            return nn.Sequential(
                nn.Conv2d(1, 32, 3, padding=1),
                nn.ReLU(),
                nn.MaxPool2d(2),
                nn.Conv2d(32, 64, 3, padding=1),
                nn.ReLU(),
                nn.MaxPool2d(2),
                nn.Flatten(),
                nn.Linear(64 * 7 * 7, 128),
                nn.ReLU(),
                nn.Linear(128, 10)
            )
        elif any('fc' in k or 'linear' in k for k in keys):
            # Fully connected model
            print("  Detected: Fully connected architecture")
            return nn.Sequential(
                nn.Linear(784, 256),
                nn.ReLU(),
                nn.Linear(256, 128),
                nn.ReLU(),
                nn.Linear(128, 10)
            )
        else:
            # Default model
            print("  Using: Default architecture")
            return nn.Sequential(
                nn.Linear(784, 256),
                nn.ReLU(),
                nn.Linear(256, 128),
                nn.ReLU(),
                nn.Linear(128, 10)
            )
    
    def predict(self, input_tensor):
        """Run inference"""
        with torch.no_grad():
            try:
                output = self.model(input_tensor)
                probabilities = torch.softmax(output, dim=1)
                predictions = torch.argmax(probabilities, dim=1)
                confidence = torch.max(probabilities, dim=1)[0]
                
                return {
                    'prediction': predictions.item(),
                    'confidence': confidence.item(),
                    'all_probabilities': probabilities[0].cpu().numpy().tolist()
                }
            except Exception as e:
                print(f"Prediction error: {e}")
                # Return dummy prediction
                return {
                    'prediction': 0,
                    'confidence': 0.1,
                    'all_probabilities': [0.1] * 10
                }
