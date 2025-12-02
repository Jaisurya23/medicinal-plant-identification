import os
import json
import numpy as np
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import logging
logging.getLogger('tensorflow').setLevel(logging.ERROR)

import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.models import Model
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from datetime import datetime

DATASET_PATH = "dataset/"
MODEL_PATH = "models/plant_model.h5"
LABELS_PATH = "models/labels.json"

def train_medicinal_plant_model():
    """
    Train a CNN model using MobileNetV2 for medicinal plant classification.
    Expected dataset structure:
    dataset/
        Amla/
            img1.jpg
            img2.jpg
        AloeVera/
            img1.jpg
        Neem/
            img1.jpg
        Tulsi/
            img1.jpg
    """
    
    # Check if dataset exists
    if not os.path.exists(DATASET_PATH):
        return "Error: Dataset folder not found! Please upload dataset first."
    
    # Check if dataset has subdirectories
    subdirs = [d for d in os.listdir(DATASET_PATH) 
               if os.path.isdir(os.path.join(DATASET_PATH, d))]
    
    if len(subdirs) == 0:
        return "Error: No plant categories found in dataset folder!"
    
    print(f"Found {len(subdirs)} plant categories: {subdirs}")
    
    # Create models directory if it doesn't exist
    os.makedirs("models", exist_ok=True)
    
    # Data augmentation for training
    train_datagen = ImageDataGenerator(
        rescale=1.0/255,
        rotation_range=30,
        width_shift_range=0.2,
        height_shift_range=0.2,
        shear_range=0.2,
        zoom_range=0.2,
        horizontal_flip=True,
        fill_mode='nearest',
        validation_split=0.2  # 80% train, 20% validation
    )
    
    # Validation data (only rescaling)
    val_datagen = ImageDataGenerator(
        rescale=1.0/255,
        validation_split=0.2
    )
    
    img_size = (224, 224)
    batch_size = 16
    
    # Load training data
    print("\n[INFO] Loading training data...")
    train_data = train_datagen.flow_from_directory(
        DATASET_PATH,
        target_size=img_size,
        batch_size=batch_size,
        class_mode='sparse',  # Use sparse for sparse_categorical_crossentropy
        subset='training',
        shuffle=True
    )
    
    # Load validation data
    print("[INFO] Loading validation data...")
    val_data = val_datagen.flow_from_directory(
        DATASET_PATH,
        target_size=img_size,
        batch_size=batch_size,
        class_mode='sparse',
        subset='validation',
        shuffle=False
    )
    
    num_classes = train_data.num_classes
    class_indices = train_data.class_indices
    
    # Save class labels
    labels = {v: k for k, v in class_indices.items()}
    with open(LABELS_PATH, 'w') as f:
        json.dump(labels, f, indent=4)
    
    print(f"\n[INFO] Number of classes: {num_classes}")
    print(f"[INFO] Class labels: {labels}")
    print(f"[INFO] Training samples: {train_data.samples}")
    print(f"[INFO] Validation samples: {val_data.samples}")
    
    # Build MobileNetV2 model
    print("\n[INFO] Building MobileNetV2 model...")
    base_model = MobileNetV2(
        weights="imagenet",
        include_top=False,
        input_shape=(224, 224, 3)
    )
    
    # Freeze base model initially
    base_model.trainable = False
    
    # Add custom classification head
    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = Dense(256, activation='relu')(x)
    x = Dropout(0.5)(x)
    x = Dense(128, activation='relu')(x)
    x = Dropout(0.3)(x)
    predictions = Dense(num_classes, activation='softmax')(x)
    
    model = Model(inputs=base_model.input, outputs=predictions)
    
    # Compile model
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    
    print("\n[INFO] Model Summary:")
    model.summary()
    
    # Callbacks
    early_stop = EarlyStopping(
        monitor='val_loss',
        patience=5,
        restore_best_weights=True,
        verbose=1
    )
    
    reduce_lr = ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.2,
        patience=3,
        min_lr=1e-7,
        verbose=1
    )
    
    # Training
    print("\n" + "="*60)
    print("TRAINING STARTED")
    print("="*60)
    
    start_time = datetime.now()
    
    history = model.fit(
        train_data,
        validation_data=val_data,
        epochs=15,
        callbacks=[early_stop, reduce_lr],
        verbose=1
    )
    
    end_time = datetime.now()
    training_time = (end_time - start_time).total_seconds()
    
    # Save model
    print(f"\n[INFO] Saving model to {MODEL_PATH}...")
    model.save(MODEL_PATH)
    
    # Print training results
    final_train_acc = history.history['accuracy'][-1]
    final_val_acc = history.history['val_accuracy'][-1]
    final_train_loss = history.history['loss'][-1]
    final_val_loss = history.history['val_loss'][-1]
    
    print("\n" + "="*60)
    print("TRAINING COMPLETED SUCCESSFULLY")
    print("="*60)
    print(f"Training Time: {training_time:.2f} seconds ({training_time/60:.2f} minutes)")
    print(f"Final Training Accuracy: {final_train_acc*100:.2f}%")
    print(f"Final Validation Accuracy: {final_val_acc*100:.2f}%")
    print(f"Final Training Loss: {final_train_loss:.4f}")
    print(f"Final Validation Loss: {final_val_loss:.4f}")
    print(f"Model saved at: {MODEL_PATH}")
    print(f"Labels saved at: {LABELS_PATH}")
    print("="*60 + "\n")
    
    return f"Training completed! Validation Accuracy: {final_val_acc*100:.2f}%"


if __name__ == '__main__':
    result = train_medicinal_plant_model()
    print(result)