# -*- coding: utf-8 -*-
"""AnimalsImageClassification

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1BXcWRNpD-KuXtKUcus7Ebm8RZ-eBEq4k

# Proyek Akhir: Image Classification Model Deployment
- Nama: Indriyati Rahmi Setyani
- Email: indriyatirs@gmail.com
- Id Dicoding: indriyatirs
- Sumber Dataset: Animals-Kaggle
- Link Kaggle: https://www.kaggle.com/datasets/antobenedetti/animals

## Import Libraries
"""

import os
import glob
import warnings
import pathlib
import cv2

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import tensorflow as tf
import itertools

from PIL import Image
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.preprocessing import image
from sklearn.metrics import confusion_matrix
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.models import Sequential
from keras.preprocessing.image import ImageDataGenerator

warnings.filterwarnings('ignore')

# download file API akun kaggle

!gdown --id 1JLVL1Hwvs6Aky4eOgPJZpPf0FiATb7H_

# membuat environment untuk menyimpan file dari kaggle

os.environ['KAGGLE_CONFIG_DIR'] = '/content'

# mendownload dataset menggunakan API dataset dari kaggle

!kaggle datasets download -d antobenedetti/animals

!unzip /content/animals.zip

"""Dataset sudah berhasil di import dari Kaggle ke dalam google colab notebook

## Load Data
"""

image_data = '/content/animals/train'
pd.DataFrame(os.listdir(image_data),columns=['Files_Name'])

image_files = [i for i in glob.glob(image_data + "//*//*")]
np.random.shuffle(image_files)
labels = [os.path.dirname(i).split("/")[-1] for i in image_files]
imgdata = zip(image_files, labels)
df_image = pd.DataFrame(imgdata, columns = ["Image", "Label"])
df_image

df_image.shape

# menampilkan resolusi gambar dari dataset
for path in df_image['Image']:
  image_name = Image.open(path)
  print(image_name.size)

df_image['Label'].value_counts()

sns.countplot(data=df_image, x='Label', palette='viridis')

plt.tick_params(axis='x', labelrotation=90)
plt.show()

"""## Image Data Generator

### Image Augmentation
"""

train_datagen = ImageDataGenerator(
                    rescale = 1./255,
                    rotation_range = 20,
                    horizontal_flip = True,
                    shear_range = 0.2,
                    fill_mode = 'nearest',
                    zoom_range=0.2,
                    validation_split = 0.2)

"""### Split Data"""

train_generator = train_datagen.flow_from_directory(
        image_data,
        target_size=(150, 150),
        class_mode='categorical',
        batch_size = 32,
        shuffle = True,
        subset = 'training'
        )

validation_generator = train_datagen.flow_from_directory(
        image_data,
        target_size=(150, 150),
        class_mode='categorical',
        shuffle = True,
        batch_size = 32,
        subset = 'validation'
        )

"""## Show Image and Label From Train Generator"""

list_labels = list(train_generator.class_indices.keys())
print(list_labels)

images, labels = next(train_generator)

plt.figure(figsize=(10, 10))
for i in range(9):
  ax = plt.subplot(3, 3, i + 1)
  plt.imshow(images[i])
  plt.title(list_labels[np.argmax(labels[i])])
  plt.axis("off")
plt.tight_layout()
plt.show()

"""## CNN Model

### Sequential Model
"""

IMG_SIZE = (150, 150)
IMG_SHAPE = IMG_SIZE + (3,)
base_model = MobileNetV2(input_shape = IMG_SHAPE,
                         include_top = False,
                         weights = 'imagenet')

for layer in base_model.layers:
  layer.trainable = False

model = tf.keras.models.Sequential([
    base_model,
    tf.keras.layers.Conv2D(64, (3, 3), padding='same', activation="relu"),
    tf.keras.layers.MaxPooling2D((2,2)),
    tf.keras.layers.Flatten(),
    tf.keras.layers.Dropout(0.5),
    tf.keras.layers.Dense(64, activation='relu'),
    tf.keras.layers.Dense(32, activation='relu'),
    tf.keras.layers.Dropout(0.2),
    tf.keras.layers.Dense(5, activation='softmax')
])
#model.layers[0].trainable = False

model.summary()

optimizer = tf.keras.optimizers.Adam(learning_rate=1.0000e-04)
model.compile(optimizer=optimizer,
              loss='categorical_crossentropy',
              metrics=["accuracy"])

"""### Model Fitting"""

class myCallback(tf.keras.callbacks.Callback):
  def on_epoch_end(self, epoch, logs={}):
    if(logs.get('val_accuracy') > 0.92) and (logs.get('accuracy') > 0.92):
      print("\nIterasi berhenti, akurasi model lebih dari 92%")
      self.model.stop_training = True

callbacks = myCallback()

training_samples = 10780
validation_samples = 2694
batch_size = 32

history = model.fit(
      train_generator,
      steps_per_epoch = training_samples // batch_size,
      epochs=30,
      validation_data=validation_generator,
      validation_steps = validation_samples // batch_size,
      callbacks=[callbacks]
      )

"""### Plotting the Model Metrics"""

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(15,5))

ax[0].plot(history.history['loss'], label='Loss')
ax[0].plot(history.history['val_loss'], label='Validation Loss')

ax[0].set_title('Loss/Validation Loss vs Epoch')
ax[0].set_xlabel('Epoch')
ax[0].set_ylabel('Loss')
ax[0].legend(loc='best')

ax[1].plot(history.history['accuracy'], label='Accuracy')
ax[1].plot(history.history['val_accuracy'], label='Validation Accuracy')

ax[1].set_title('Accuracy/Validation Accuracy vs Epoch')
ax[1].set_xlabel('Epoch')
ax[1].set_ylabel('Accuracy')
ax[1].legend(loc='best')

plt.tight_layout()
plt.show()

"""## Confusion Matrix

Dataset yang digunakan berasal dari folder yang berbeda
"""

test = '/content/animals/val'

test_datagen = ImageDataGenerator(
                    rescale = 1./255)

test_generator = test_datagen.flow_from_directory(
        test,
        target_size=(150, 150),
        class_mode='categorical',
        shuffle = False,
        batch_size = 32
        )

predictions = model.predict(test_generator)
y_pred = np.argmax(predictions, axis=1)
y_true = test_generator.classes
labels = {v:k for k, v in train_generator.class_indices.items()}

cf_mtx = confusion_matrix(y_true, y_pred)

group_counts = ["{0:0.0f}".format(value) for value in cf_mtx.flatten()]
box_labels = [v for v in group_counts]
box_labels = np.asarray(box_labels).reshape(5, 5)

plt.figure(figsize = (8, 6))
sns.heatmap(cf_mtx, xticklabels=labels.values(), yticklabels=labels.values(),
           cmap=plt.cm.Blues, fmt="", annot=box_labels)

plt.title('Confusion Matrix')
plt.xlabel('Predicted Label')
plt.ylabel('True Label')
plt.tight_layout()
plt.show()

"""## Image Prediction"""

val_files = [i for i in glob.glob(test + "//*//*")]
np.random.shuffle(val_files)
val_labels = [os.path.dirname(i).split("/")[-1] for i in image_files]
imgval = zip(val_files, val_labels)
val_df = pd.DataFrame(imgval, columns = ["Image", "Label"])
val_df

testdf = val_df.sample(n = 10, random_state=42)

for path in testdf['Image']:
  images_test = image.load_img(path)

  img = cv2.imread(path)
  img = cv2.resize(img, (150,150))
  img = np.reshape(img, [1,150,150,3])
  img = img/255

  pred = model.predict(img)
  max_idx = np.argmax(pred)

  class_label = list(train_generator.class_indices.keys())
  predicted_label = class_label[max_idx]
  plt.imshow(images_test)
  plt.title(f'Predicted: {predicted_label}')
  plt.show()

"""## Save Model"""

export_dir = 'saved_model/'
tf.saved_model.save(model, export_dir)

converter = tf.lite.TFLiteConverter.from_saved_model(export_dir)
tflite_model = converter.convert()

tflite_model_file = pathlib.Path('animals_classification.tflite')
tflite_model_file.write_bytes(tflite_model)