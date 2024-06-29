import numpy as np
import pandas as pd
import tensorflow as tf
import matplotlib.pyplot as plt

from tensorflow import keras
from keras.layers import (
    Bidirectional, LSTM, Dense, Flatten
)
from keras.optimizers import (
    Adam, RMSprop, SGD
)

class CustomCallback(tf.keras.callbacks.Callback):
    def on_epoch_end(self, epoch, logs={}):
        if(logs.get('val_accuracy') >= 0.975 or logs.get('loss') <= 0.015):
            # Stop if threshold is met
            print(f"\nThreshold met! until epoch {epoch}")
            self.model.stop_training = True

def create_model(input_shape, optimizer='adam'):
    model = tf.keras.models.Sequential([
        tf.keras.layers.Input(shape=(input_shape)),
        tf.keras.layers.LSTM(64, return_sequences=True),
        tf.keras.layers.LSTM(32),
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(64, activation=tf.nn.relu),
        tf.keras.layers.Dropout(0.1),
        tf.keras.layers.Dense(32, activation=tf.nn.relu, kernel_regularizer=tf.keras.regularizers.L2(l2=0.01)),
        tf.keras.layers.Dense(16, activation=tf.nn.relu),
        tf.keras.layers.Dense(2, activation=tf.nn.softmax)
    ])

    model.compile(optimizer=optimizer,
                    loss='sparse_categorical_crossentropy',
                    metrics=['accuracy']
                  )

    return model

def train_model(X_train, y_train, X_test, y_test, epochs=30):
    model = create_model()

    history = model.fit(
        X_train, y_train,
        epochs=epochs,
        validation_date=(X_test, y_test),
        callbacks=[CustomCallback()]
        )

    return model, history

def plot_learning_curve(history):
    acc = history.history['accuracy']
    loss = history.history['loss']

    epochs = range(len(acc))

    val_acc = history.history['val_accuracy']
    val_loss = history.history['val_loss']

    plt.plot(epochs, acc, 'b', label="Training Accuracy")
    plt.plot(epochs, val_acc, 'r', label="Validation Accuracy")
    plt.title("Training vs Validation Accuracy")
    plt.legend(loc=0)
    plt.figure()
    plt.show()

    plt.plot(epochs, loss, 'b', label="Training Loss")
    plt.plot(epochs, val_loss, 'r', label="Validation Loss")
    plt.title("Training vs Validation Loss")
    plt.legend(loc=0)
    plt.figure()
    plt.show()