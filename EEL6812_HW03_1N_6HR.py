# -*- coding: utf-8 -*-
"""EEL6812 - HW03 1N_6HR.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/15eqT-8Scsd_y1qyKSABudFUaVsYAkEsO
"""

# STUDENT: MOLTO, JOAQUIN (PID: 6119985)
# COURSE: EEL6812 - ADVANCED TOPICS IN NEURAL NETWORKS (DEEP LEARNING)
# ASSIGNMENT #3: RECURRENT NEURAL NETWORK AND LONG SHORT-TERM MEMORY NETWORKS
# DUE DATE: 04/26/2024

"""---

<center> RETRIEVING DATA FROM <b>GEFCOM2014(E,V2)</b> AND PREPARING IT FOR THE RNN/LSTM </center>

---
"""

# THE FIRST PORTION OF THIS JUPYTER NOTEBOOK (.IPYNB) WAS PROVIDED BY DR. BARRETO FOR DATA EXTRACTION AND PREPROCESSING
# IT WILL BE USED AS A HELPER IN DEVELOPING THE RNN AND LSTM SOLUTIONS PER THE PROBLEM SPECIFICATION

# Commented out IPython magic to ensure Python compatibility.
# IMPORT NECESSARY LIBRARIES
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
# plt.style.use('./rose-pine-moon.mplstyle')
import os
import shutil
import matplotlib.pyplot as plt
# %matplotlib inline
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import ModelCheckpoint, LambdaCallback, EarlyStopping
import sklearn
from sklearn.metrics import mean_absolute_error

!wget https://www.dropbox.com/s/pqenrr2mcvl0hk9/GEFCom2014.zip # retrieve the zip file from the Internet from the given URL

!unzip GEFCom2014.zip # OS-level command to unzip the file brought into the Google Colab temporary file ecosystem

!ls -l # UNIX command to list files in directory, passing the -l flag (long)

!ls -l 'GEFCom2014 Data'/

"""##### We want to use **GEFCom2014-E_V2.zip** for this project"""

!mv  'GEFCom2014 Data'/GEFCom2014-E_V2.zip  ./ # let's bring it to the top level before unzipping it

!unzip GEFCom2014-E_V2.zip

!ls -l # we can now verify that we loaded the file GEFCom2014-E.xlsx

GEFDF = pd.read_excel('GEFCom2014-E.xlsx', skiprows=range(1, 17545), dtype = {'A':np.int32  ,'B':np.int8   ,'C':np.int32  ,'D':np.float64}, index_col = None ) # CONVERT GEFCom2014-E.xlsx to a PANDAS DATAFRAME called GEFDF

print(GEFDF) # we can "see" the Pandas DataFrame (called GEFDF) that has been obtained

# WRITING OUT THE GEFDF DATAFRAME TO A TEXT (CSV) FILE
GEFDF.to_csv('GEF14.csv',  encoding='utf-8', index=False, header=True, columns=['Hour','load','T'],lineterminator='\n' )
with open('GEF14.csv') as f:
    lines = f.readlines()
    last = len(lines) - 1
    lines[last] = lines[last].replace('\r','').replace('\n','')
with open('GEF14.csv', 'w') as wr:
    wr.writelines(lines)

!ls -l ./ # verifying we have created the csv file GEF14.csv

# THIS CODE CELL IS ESSENTIALLY THE SAME AS IN THE EXAMPLE FROM CH. 10 IN BOOK
import os
fname = os.path.join("GEF14.csv")

with open(fname) as f:
    data = f.read()

lines = data.split("\n")
header = lines[0].split(",")
lines = lines[1:]
print(header)
print(len(lines))

# VERY SIMILAR TO THE CORRESPONDING C0DE CELL FROM CHAPTER 10 IN BOOK
# eload (electric load) is the timeseries we will predict
# tempf (temperature in Fahrenheit) is the temperature at the same time
# import numpy as np
eload = np.zeros((len(lines),))
tempf = np.zeros((len(lines),))
raw_data = np.zeros((len(lines), len(header)-2))   #chgd )-1  to )-2 to also
# remove the HOUR column, in addition to the DATE column
print(len(lines))

for m in range(78888):
    thisline  = lines[m]
    values = [float(x) for x in thisline.split(",")[1:]]
    eload[m] = values[0]         #Captures JUST E LOAD
    tempf[m] = values[1]            #Captures JUST TEMPF
    raw_data[m] = values[0]         #Like this, raw_data Captures JUST E LOAD
    # raw_data[m, :] = values[:]   # Like this, raw_data CAPTURES BOTH

plt.plot(range(len(eload)), eload)

plt.plot(range(len(tempf)), tempf)

num_train_samples = int(0.5 * len(raw_data))
num_val_samples = int(0.25 * len(raw_data))
num_test_samples = len(raw_data) - num_train_samples - num_val_samples
print("num_train_samples:", num_train_samples)
print("num_val_samples:", num_val_samples)
print("num_test_samples:", num_test_samples)

# Display the ELOAD for the first 10 days
plt.plot(range(240),eload[:240])

# Display the tempf for the first 10 days
plt.plot(range(240),tempf[:240])

"""##### Normalize the Data $(\dfrac{X-\mu}{\sigma})$


*   This will ensure the underlying patterns behind the data are still present
while downscaling its magnitude; making it more palatable to the Neural Network


"""

mean = raw_data[:num_train_samples].mean(axis=0)
raw_data -= mean # Value - Mean / Standard Deviation
std = raw_data[:num_train_samples].std(axis=0)
raw_data /= std

"""##### Instantiating TensorFlow (TF) Datasets for Training [TR], Validation [TT], and Testing [TS]"""

# LETS JUST USE ELOAD TO FORECAST ELOAD
# THIS TIME, ( 1-input case)
# NOTE: THIS CODE HAS TO BE MODIFIED FOR THE 2-INPUT CASE, WHICH ALSO TAKES INTO CONSIDERATION THE OBSERVATIONS FROM THE TEMPERATURE (F) DATA
from tensorflow import keras

horizon = 6       # num. of hours ahead for forecast
sampling_rate = 1 # this should be kept as 1, as the sampling is already hourly
sequence_length = 30
delay = sampling_rate * (sequence_length + horizon - 1)
batch_size = 128

train_dataset = keras.utils.timeseries_dataset_from_array(
    raw_data[:-delay],
    targets=raw_data[delay:], # this would used "Normalized Targets"
    # targets=eload[delay:], # this would used "Not-normalized eload targets"
    sampling_rate=sampling_rate,
    sequence_length=sequence_length,
    shuffle=True,                  # changed to false JUST FOR VERIFICATION
    batch_size= num_train_samples,
    start_index=0,
    end_index=num_train_samples)

val_dataset = keras.utils.timeseries_dataset_from_array(
    raw_data[:-delay],    # changed from raw_data to just eload not really
    targets=raw_data[delay:],  # this would used "Normalized Targets"
    # targets=eload[delay:], # this would used "Not-normalized eload targets"
    sampling_rate=sampling_rate,
    sequence_length=sequence_length,
    shuffle=True,
    batch_size=num_val_samples,
    start_index=num_train_samples,
    end_index=num_train_samples + num_val_samples)

test_dataset = keras.utils.timeseries_dataset_from_array(
    raw_data[:-delay],     # changed from raw_data to just eload
    targets=raw_data[delay:],  # this would used "Normalized Targets"
    # targets=eload[delay:], # this would used "Not-normalized eload targets"
    sampling_rate=sampling_rate,
    sequence_length=sequence_length,
    shuffle=False,
    batch_size=num_test_samples,
    start_index=num_train_samples + num_val_samples)

"""##### Inspecting the Output of one of the Datasets"""

for samples, targets in train_dataset:
    print("samples shape:", samples.shape)
    print("targets shape:", targets.shape)
    break

"""---

<center> END OF DATA PREPARATION </center>

---

---

<center> <b>[PART II.]</b> DESIGNING THE "1-INPUT (ELOAD)" PREDICTORS </center>

---

* This part of the project calls for the creation of a model that will predict the future amount of electrical energy demand or "load" (<i><u>eload</u></i>) with a prediction horizon of 3 hours into the future and 6 hours into the future. Therefore, we will have two "1-input" models for this part:

1.   1N_3HR
2.   1IN_6HR

* Per the instructions, we need AT LEAST ONE Long Short-Term Memory (LSTM) layer in our Recurrent Neural Network (RNN). Whether to use Recurrent Dropout or not is optional; however, it might improve generalization and performance. However, this comes at the cost of slow computation time due to the incompatibility with CuDNN (CUDA Deep Neural Network) Library.
"""

max_value = float('-inf') # initialize variable for maximum value as negative infinity -∞
min_value = float('inf') # initialize variable for maximum value as positive infinity +∞

# Iterate over each batch in the dataset
for _, targets in test_dataset:
    # Find the maximum and minimum in the targets
    current_max = tf.reduce_max(targets * std + mean)
    current_min = tf.reduce_min(targets * std + mean)

    # Update the maximum and minimum values across all batches
    max_value = max(max_value, current_max.numpy())  # Update the overall max
    min_value = min(min_value, current_min.numpy())  # Update the overall min
full_range = max_value - min_value
print("MAX ELOAD IN TEST_DATASET:", max_value)
print("MIN ELOAD IN TEST_DATASET:", min_value)
print("FULL-RANGE OF ELOAD IN TEST_DATASET:", full_range)

"""---

<center> <b>[PART IIB.]</b> DESIGNING THE "1-INPUT (ELOAD)" PREDICTOR FOR "6-HOUR HORIZON" </center>

---

"""

# INITIALIZE THE SIZE/DIMENSIONS OF INPUT AND OUTPUT
output_units = 1 # will only output 1 prediction

model = Sequential([
    LSTM(100, return_sequences=True),
    Dropout(0.1),  # Apply dropout separately
    LSTM(100),
    Dense(output_units)
])

# COMPILE THE MODEL
model.compile(optimizer='adam', loss='mse',metrics=['mae'])

# CALLBACKS FOR MONITORING AND PLOTTING
val_loss_checkpoint = ModelCheckpoint('best_model.keras', monitor='val_loss', verbose=1, save_best_only=True, mode='min')
# CALLBACK FOR EARLY STOPPING
early_stopping = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)

# Function to store metrics and plot them after training
def plot_metrics(history):
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))  # Create a figure with subplots arranged in 2x2

    # Plot for full history
    axes[0, 0].plot(history['loss'], color='blue', linestyle='-', marker='o', label='Training Loss')
    axes[0, 0].plot(history['val_loss'], color='orange', linestyle='--', marker='^', label='Validation Loss')
    axes[0, 0].set_title('Training and Validation Loss')
    axes[0, 0].set_xlabel('Epoch')
    axes[0, 0].set_ylabel('Loss')
    axes[0, 0].legend()
    axes[0, 0].grid(True)

    axes[0, 1].plot(history['mae'], color='blue', linestyle='-', marker='o', label='Training MAE')
    axes[0, 1].plot(history['val_mae'], color='orange', linestyle='--', marker='^', label='Validation MAE')
    axes[0, 1].set_title('Training and Validation MAE')
    axes[0, 1].set_xlabel('Epoch')
    axes[0, 1].set_ylabel('MAE')
    axes[0, 1].legend()
    axes[0, 1].grid(True)

    # Find the epoch with the best validation loss
    best_epoch = np.argmin(history['val_loss'])

    # Plot for clipped history up to best validation loss
    axes[1, 0].plot(history['loss'][:best_epoch+1], color='blue', linestyle='-', marker='o', label='Training Loss')
    axes[1, 0].plot(history['val_loss'][:best_epoch+1], color='orange', linestyle='--', marker='^', label='Validation Loss')
    axes[1, 0].set_title('Clipped Training and Validation Loss')
    axes[1, 0].set_xlabel('Epoch')
    axes[1, 0].set_ylabel('Loss')
    axes[1, 0].legend()
    axes[1, 0].grid(True)

    axes[1, 1].plot(history['mae'][:best_epoch+1], color='blue', linestyle='-', marker='o', label='Training MAE')
    axes[1, 1].plot(history['val_mae'][:best_epoch+1], color='orange', linestyle='--', marker='^', label='Validation MAE')
    axes[1, 1].set_title('Clipped Training and Validation MAE')
    axes[1, 1].set_xlabel('Epoch')
    axes[1, 1].set_ylabel('MAE')
    axes[1, 1].legend()
    axes[1, 1].grid(True)

    plt.tight_layout()
    plt.show()

# TRAIN THE MODEL WITH CALLBACKS
history = model.fit(train_dataset, epochs=200, validation_data=val_dataset,
                    callbacks=[val_loss_checkpoint, early_stopping])

# AFTER THE TRAINING IS COMPLETE, PLOT THE METRICS USING THE HISTORY OBJECT
plot_metrics(history.history)

# PRINT THE MODEL SUMMARY
model.summary()

predictions = model.predict(test_dataset) # this will return the predictions in the scale of the normalized/standardized data

"""##### De-Normalize the Data $(X*\sigma+\mu)$


*   Return the predictions array back to its original form when analyzing the $MAE$ and $PMAE$
"""

predictions_original_scale = predictions * std + mean

for samples, targets in test_dataset.take(1):
    print("Samples: \n", samples.numpy() * std + mean)
    print("Targets: \n", targets.numpy() * std + mean)

target_values = []
for batch in test_dataset:
  targets = batch[1]
  target_values.extend(targets * std + mean)
target_values = np.array(target_values)
print("targets_values shape: ", target_values.shape)

"""$MAE=\sum_{i=1}^{n}\dfrac{\vert y_{i}-x_{i}\vert}{n}$

Where:

$MAE$=Mean Absolute Error \\
$x_{i}$=i$^{th}$ Input Sample/Pattern \\
$y_{i}$=i$^{th}$ Target Respective to Input \\
$n$=Total Number of Data Points
"""

mae = mean_absolute_error(target_values, predictions_original_scale)
print("MAE on the Test Set:", mae)

"""$PMAE=\dfrac{MAE_{[TS]}}{FR_{[TS]}}$"""

pmae = (mae / full_range) * 100
print("Percentage Mean Absolute Error (PMAE):", pmae)

# TIMESERIES PLOT OF PREDICTED VALUES BY MODEL
plt.figure(figsize=(10, 4))
plt.plot(predictions_original_scale, 'r', label='Predictions')
plt.title('Time Series of Predictions')
plt.xlabel('Sample')
plt.ylabel('Predicted Value')
plt.legend()
plt.show()

# TIMESERIES PLOT OF CORRESPONDING TARGETS
plt.figure(figsize=(10, 4))
plt.plot(target_values, 'b', label='Actual Targets')
plt.title('Time Series of Actual Targets')
plt.xlabel('Sample')
plt.ylabel('Target Value')
plt.legend()
plt.show()

# OVERLAY PLOT OF PREDICTIONS (RED SOLID LINE) AND TARGETS (BLUE SOLID LINE) (6,000:6,500)
plt.figure(figsize=(10, 4))
plt.plot(predictions_original_scale[6000:6501], 'r', label='Predictions', linestyle='-')
plt.plot(target_values[6000:6501], 'b', label='Actual Targets', linestyle='-')
plt.title('Overlay of Predictions and Targets')
plt.xlabel('Sample Index')
plt.ylabel('Value')
plt.legend()
plt.show()