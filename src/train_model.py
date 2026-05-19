import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv1D, Dense, Flatten, Dropout, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from sklearn.model_selection import train_test_split

# ==========================
# SETTINGS
SEQ_LEN = 50          # Must match collected sequences
NUM_CLASSES = 4       # Number of fault types
BATCH_SIZE = 32
EPOCHS = 100
MODEL_NAME = "dc_fault_model_v3.tflite"
VALIDATION_SPLIT = 0.1
# ==========================

# 1️⃣ LOAD DATA
X = np.load("data.npy")   # shape: (num_samples, SEQ_LEN)
y = np.load("labels.npy") # shape: (num_samples,)

# Reshape for Conv1D
X = X.reshape(-1, SEQ_LEN, 1)

# 2️⃣ SPLIT DATA
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# 3️⃣ BUILD MODEL
model = Sequential([
    Conv1D(32, kernel_size=3, activation='relu', input_shape=(SEQ_LEN,1)),
    BatchNormalization(),
    Conv1D(64, kernel_size=3, activation='relu'),
    BatchNormalization(),
    Conv1D(128, kernel_size=3, activation='relu'),
    BatchNormalization(),
    Flatten(),
    Dense(128, activation='relu'),
    Dropout(0.3),
    Dense(NUM_CLASSES, activation='softmax')
])

model.compile(
    optimizer='adam',
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)

model.summary()

# 4️⃣ CALLBACKS
callbacks = [
    EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True),
    ModelCheckpoint("best_model_v3.h5", monitor='val_loss', save_best_only=True)
]

# 5️⃣ TRAIN
history = model.fit(
    X_train, y_train,
    validation_split=VALIDATION_SPLIT,
    epochs=EPOCHS,
    batch_size=BATCH_SIZE,
    callbacks=callbacks
)

# 6️⃣ EVALUATE
loss, acc = model.evaluate(X_test, y_test)
print(f"✅ Test Accuracy: {acc*100:.2f}%")

# 7️⃣ CONVERT TO TFLITE
converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()

with open(MODEL_NAME, "wb") as f:
    f.write(tflite_model)

print(f"✅ TFLite model saved as {MODEL_NAME}")
