"""
Standalone script to test the trained model without Flask
This script allows you to:
1. Test a single image
2. Test multiple images from a folder
3. Evaluate model performance on validation data
4. Generate confusion matrix and accuracy report
"""

import os
import json
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import tensorflow as tf

# Suppress warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import logging
logging.getLogger('tensorflow').setLevel(logging.ERROR)

MODEL_PATH = "models/plant_model.h5"
LABELS_PATH = "models/labels.json"
DATASET_PATH = "dataset/"


def load_trained_model():
    """Load the trained model and labels."""
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Model not found at {MODEL_PATH}")
        print("Please train the model first using: python train_model.py")
        return None, None
    
    if not os.path.exists(LABELS_PATH):
        print(f"❌ Labels not found at {LABELS_PATH}")
        return None, None
    
    print("📂 Loading model...")
    model = load_model(MODEL_PATH)
    print("✅ Model loaded successfully!")
    
    with open(LABELS_PATH, 'r') as f:
        labels = json.load(f)
    print(f"✅ Labels loaded: {labels}\n")
    
    return model, labels


def preprocess_single_image(img_path, target_size=(224, 224)):
    """Preprocess a single image for prediction."""
    img = image.load_img(img_path, target_size=target_size)
    img_array = image.img_to_array(img)
    img_array = img_array / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    return img_array


def predict_single_image(model, labels, img_path, show_all=True):
    """
    Test the model on a single image.
    
    Args:
        model: Trained Keras model
        labels: Dictionary mapping class indices to names
        img_path: Path to the image file
        show_all: If True, show all class probabilities
    """
    print("="*70)
    print(f"🔍 Testing Image: {img_path}")
    print("="*70)
    
    if not os.path.exists(img_path):
        print(f"❌ Image not found: {img_path}")
        return
    
    # Preprocess
    img_array = preprocess_single_image(img_path)
    
    # Predict
    predictions = model.predict(img_array, verbose=0)
    
    # Get results
    predicted_class = np.argmax(predictions[0])
    confidence = predictions[0][predicted_class] * 100
    plant_name = labels[str(predicted_class)]
    
    # Display results
    print(f"\n🌿 PREDICTION: {plant_name}")
    print(f"📊 CONFIDENCE: {confidence:.2f}%")
    print(f"{'='*70}")
    
    if show_all:
        print("\n📋 All Class Probabilities:")
        print("-" * 70)
        # Sort by probability
        sorted_predictions = sorted(
            [(labels[str(i)], prob * 100) for i, prob in enumerate(predictions[0])],
            key=lambda x: x[1],
            reverse=True
        )
        
        for plant, prob in sorted_predictions:
            bar_length = int(prob / 2)  # Scale for display
            bar = "█" * bar_length
            print(f"{plant:15s} | {bar:50s} | {prob:6.2f}%")
    
    print("="*70 + "\n")
    return plant_name, confidence


def test_multiple_images(model, labels, folder_path):
    """
    Test the model on multiple images from a folder.
    
    Args:
        model: Trained Keras model
        labels: Dictionary mapping class indices to names
        folder_path: Path to folder containing test images
    """
    print("="*70)
    print(f"📁 Testing Multiple Images from: {folder_path}")
    print("="*70 + "\n")
    
    if not os.path.exists(folder_path):
        print(f"❌ Folder not found: {folder_path}")
        return
    
    # Get all image files
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    image_files = [f for f in os.listdir(folder_path) 
                   if os.path.splitext(f)[1].lower() in image_extensions]
    
    if not image_files:
        print(f"❌ No images found in {folder_path}")
        return
    
    print(f"Found {len(image_files)} images\n")
    
    results = []
    
    for img_file in image_files:
        img_path = os.path.join(folder_path, img_file)
        plant_name, confidence = predict_single_image(model, labels, img_path, show_all=False)
        results.append((img_file, plant_name, confidence))
    
    # Summary
    print("\n" + "="*70)
    print("📊 SUMMARY OF ALL PREDICTIONS")
    print("="*70)
    print(f"{'Image':<30s} | {'Prediction':<15s} | {'Confidence'}")
    print("-"*70)
    
    for img_file, plant_name, confidence in results:
        print(f"{img_file:<30s} | {plant_name:<15s} | {confidence:6.2f}%")
    
    print("="*70 + "\n")


def evaluate_on_validation_set(model, labels):
    """
    Evaluate the model on validation dataset.
    Shows accuracy, confusion matrix, and per-class accuracy.
    """
    print("="*70)
    print("📊 EVALUATING MODEL ON VALIDATION SET")
    print("="*70 + "\n")
    
    if not os.path.exists(DATASET_PATH):
        print(f"❌ Dataset not found at {DATASET_PATH}")
        return
    
    # Create validation data generator
    val_datagen = ImageDataGenerator(
        rescale=1.0/255,
        validation_split=0.2
    )
    
    val_data = val_datagen.flow_from_directory(
        DATASET_PATH,
        target_size=(224, 224),
        batch_size=16,
        class_mode='sparse',
        subset='validation',
        shuffle=False
    )
    
    print(f"Validation samples: {val_data.samples}\n")
    
    # Evaluate
    print("⏳ Evaluating model...")
    loss, accuracy = model.evaluate(val_data, verbose=1)
    
    print("\n" + "="*70)
    print(f"✅ Validation Accuracy: {accuracy*100:.2f}%")
    print(f"📉 Validation Loss: {loss:.4f}")
    print("="*70 + "\n")
    
    # Get predictions for confusion matrix
    print("📊 Generating detailed metrics...")
    predictions = model.predict(val_data, verbose=1)
    predicted_classes = np.argmax(predictions, axis=1)
    true_classes = val_data.classes
    
    # Calculate per-class accuracy
    print("\n" + "="*70)
    print("📋 PER-CLASS ACCURACY")
    print("="*70)
    
    class_indices = val_data.class_indices
    # Reverse the dictionary
    idx_to_class = {v: k for k, v in class_indices.items()}
    
    for class_idx in sorted(idx_to_class.keys()):
        class_name = idx_to_class[class_idx]
        
        # Get indices for this class
        class_mask = true_classes == class_idx
        class_predictions = predicted_classes[class_mask]
        class_true = true_classes[class_mask]
        
        # Calculate accuracy
        correct = np.sum(class_predictions == class_true)
        total = len(class_true)
        class_accuracy = (correct / total * 100) if total > 0 else 0
        
        print(f"{class_name:15s} | Accuracy: {class_accuracy:6.2f}% | ({correct}/{total} correct)")
    
    print("="*70 + "\n")
    
    # Simple confusion matrix
    print("="*70)
    print("🔢 CONFUSION MATRIX")
    print("="*70)
    print("(Rows: True Labels, Columns: Predicted Labels)\n")
    
    num_classes = len(class_indices)
    confusion = np.zeros((num_classes, num_classes), dtype=int)
    
    for true_label, pred_label in zip(true_classes, predicted_classes):
        confusion[true_label][pred_label] += 1
    
    # Print header
    print(" " * 15, end=" | ")
    for idx in sorted(idx_to_class.keys()):
        print(f"{idx_to_class[idx][:10]:>10s}", end=" | ")
    print("\n" + "-" * (15 + (num_classes * 13)))
    
    # Print matrix
    for idx in sorted(idx_to_class.keys()):
        print(f"{idx_to_class[idx][:15]:15s}", end=" | ")
        for pred_idx in sorted(idx_to_class.keys()):
            print(f"{confusion[idx][pred_idx]:10d}", end=" | ")
        print()
    
    print("="*70 + "\n")


def main_menu():
    """Interactive menu for testing the model."""
    model, labels = load_trained_model()
    
    if model is None or labels is None:
        return
    
    while True:
        print("\n" + "="*70)
        print("🧪 MODEL TESTING MENU")
        print("="*70)
        print("1. Test single image")
        print("2. Test multiple images from folder")
        print("3. Evaluate on validation set")
        print("4. Quick test on sample images")
        print("5. Exit")
        print("="*70)
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            img_path = input("\nEnter image path: ").strip()
            predict_single_image(model, labels, img_path)
            
        elif choice == '2':
            folder_path = input("\nEnter folder path: ").strip()
            test_multiple_images(model, labels, folder_path)
            
        elif choice == '3':
            evaluate_on_validation_set(model, labels)
            
        elif choice == '4':
            # Quick test with sample images if they exist
            test_folders = ['test_images', 'dataset/Amla', 'dataset/AloeVera', 
                           'dataset/Neem', 'dataset/Tulsi']
            
            for folder in test_folders:
                if os.path.exists(folder):
                    files = [f for f in os.listdir(folder) 
                            if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                    if files:
                        # Test first image from folder
                        img_path = os.path.join(folder, files[0])
                        predict_single_image(model, labels, img_path, show_all=True)
                        break
            else:
                print("❌ No test images found in common folders")
                
        elif choice == '5':
            print("\n👋 Exiting... Good luck with your project!")
            break
            
        else:
            print("❌ Invalid choice. Please enter 1-5.")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🌿 MEDICINAL PLANT MODEL TESTER")
    print("="*70)
    print("This script tests your trained model without running Flask")
    print("="*70 + "\n")
    
    # Check if running directly
    import sys
    
    if len(sys.argv) > 1:
        # Command line mode
        if sys.argv[1] == 'eval':
            model, labels = load_trained_model()
            if model:
                evaluate_on_validation_set(model, labels)
        elif sys.argv[1] == 'test' and len(sys.argv) > 2:
            model, labels = load_trained_model()
            if model:
                predict_single_image(model, labels, sys.argv[2])
        else:
            print("Usage:")
            print("  python test_model.py              # Interactive menu")
            print("  python test_model.py eval         # Evaluate on validation set")
            print("  python test_model.py test <path>  # Test single image")
    else:
        # Interactive mode
        main_menu()