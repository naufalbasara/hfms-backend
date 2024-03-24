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
        desired_metrics = 0.8
        if logs.get('accuracy') > desired_metrics and logs.get('val_accuracy') > desired_metrics:
            print(f"Desired metrics reached with accuracy {logs.get('accuracy')}. Stopping training.. ")
            self.model.stop_training=True
        return

def predictive_model(input_shape, learning_rate=0.001):
    input_layer = tf.keras.layers.Input(shape=(input_shape))
    hidden_layer_1 = Bidirectional(LSTM(32))(input_layer)
    hidden_layer_2 = Bidirectional(LSTM(32))(hidden_layer_1)
    hidden_layer_3 = Flatten()(hidden_layer_2)
    hidden_layer_4 = Dense(units=128)(hidden_layer_3)
    output_layeur = Dense(units=1, activation=tf.nn.sigmoid())(hidden_layer_4)

    model = tf.keras.Model(input_layer, output_layeur)
    model.compile(
        loss='binary_crossentropy',
        optimizer=Adam(learning_rate=learning_rate),
        metrics=['accuracy']
    )

    return model

def train_model(X_train, y_train, X_test, y_test, epochs=30):
    model = predictive_model()

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