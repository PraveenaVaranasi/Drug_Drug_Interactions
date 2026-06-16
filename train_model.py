"""
Quick training script to create a properly trained model checkpoint
"""
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
import json
import sys

sys.path.insert(0, '/Users/tb266/Bhavani_project')
from model_drug_detection import DrugDetectionModel

def create_synthetic_training_data(num_samples=500):
    """Create synthetic training data for model training
    
    Generates balanced safe and harmful samples:
    - Safe (0): Drugs with low similarity (different feature distributions)
    - Harmful (1): Drugs with high similarity (overlapping features)
    """
    print(f"Creating {num_samples} synthetic training samples...")
    print(f"  - Ensuring balanced Safe (0) and Harmful (1) labels")
    
    # Split samples equally between safe and harmful
    num_safe = num_samples // 2
    num_harmful = num_samples - num_safe
    
    drug1_vectors = np.random.randn(num_samples, 2048).astype(np.float32)
    drug2_vectors = np.zeros((num_samples, 2048), dtype=np.float32)
    labels = np.zeros(num_samples, dtype=np.int64)
    
    # Generate SAFE samples (label=0): low similarity between drugs
    print(f"  Generating {num_safe} SAFE samples (dissimilar drug pairs)...")
    for i in range(num_safe):
        # Generate completely independent vectors for safe pairs
        drug2_vectors[i] = np.random.randn(2048).astype(np.float32)
        # Ensure they're dissimilar by checking distance
        while np.linalg.norm(drug1_vectors[i] - drug2_vectors[i]) < 20:
            drug2_vectors[i] = np.random.randn(2048).astype(np.float32)
        labels[i] = 0  # Safe
    
    # Generate HARMFUL samples (label=1): high similarity between drugs
    print(f"  Generating {num_harmful} HARMFUL samples (similar drug pairs)...")
    for i in range(num_safe, num_samples):
        # Generate similar vectors for harmful pairs by adding small noise
        noise_scale = np.random.uniform(0.05, 0.15)  # Controlled noise
        drug2_vectors[i] = drug1_vectors[i] + np.random.randn(2048).astype(np.float32) * noise_scale
        labels[i] = 1  # Harmful
    
    # Shuffle all samples while keeping labels aligned
    shuffle_idx = np.random.permutation(num_samples)
    drug1_vectors = drug1_vectors[shuffle_idx]
    drug2_vectors = drug2_vectors[shuffle_idx]
    labels = labels[shuffle_idx]
    
    # Concatenate and trim to 2097
    combined = np.concatenate([drug1_vectors, drug2_vectors], axis=1)[:, :2097]
    
    print(f"  Dataset balance: {np.sum(labels==0)} Safe, {np.sum(labels==1)} Harmful")
    
    return torch.from_numpy(combined), torch.from_numpy(labels).long()

def train_model(model, train_loader, num_epochs=10):
    """Train the model"""
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.to(device)
    model.train()
    
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    for epoch in range(num_epochs):
        total_loss = 0
        correct = 0
        total = 0
        
        for X_batch, y_batch in train_loader:
            X_batch, y_batch = X_batch.to(device), y_batch.to(device)
            
            optimizer.zero_grad()
            outputs = model(X_batch)
            loss = criterion(outputs, y_batch)
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += y_batch.size(0)
            correct += (predicted == y_batch).sum().item()
        
        accuracy = 100 * correct / total
        avg_loss = total_loss / len(train_loader)
        print(f"Epoch [{epoch+1}/{num_epochs}] Loss: {avg_loss:.4f}, Accuracy: {accuracy:.2f}%")
    
    return model

def main():
    print("Training Drug Detection Model...")
    print("=" * 50)
    
    # Create synthetic data
    X, y = create_synthetic_training_data(num_samples=500)
    dataset = TensorDataset(X, y)
    train_loader = DataLoader(dataset, batch_size=32, shuffle=True)
    
    # Create model
    print("\nInitializing model...")
    model = DrugDetectionModel(input_size=2097)
    
    # Train model
    print("\nTraining model...")
    model = train_model(model, train_loader, num_epochs=10)
    
    # Save as standard checkpoint
    checkpoint_path = "best_model_trained.pth"
    print(f"\nSaving checkpoint to {checkpoint_path}...")
    torch.save({
        'model_state_dict': model.state_dict(),
        'model_architecture': 'DrugDetectionModel',
        'input_size': 2097,
        'class_names': ['Safe', 'Harmful'],
        'training_info': {
            'num_samples': 500,
            'num_epochs': 10,
            'optimizer': 'Adam',
            'loss_fn': 'CrossEntropyLoss'
        }
    }, checkpoint_path)
    print(f"✓ Model saved successfully!")
    
    # Test inference
    print("\nTesting inference...")
    model.eval()
    test_input = torch.randn(1, 2097)
    with torch.no_grad():
        output = model(test_input)
        probs = torch.softmax(output, dim=1)
        pred = torch.argmax(probs, dim=1)
        conf = torch.max(probs, dim=1)[0]
    
    print(f"Test input prediction: {pred.item()} (Safe=0, Harmful=1)")
    print(f"Confidence: {conf.item()*100:.2f}%")
    print(f"Probabilities: {probs[0].cpu().numpy()}")

if __name__ == "__main__":
    main()
