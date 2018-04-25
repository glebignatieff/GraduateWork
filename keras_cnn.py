import os
import common

import matplotlib.pyplot as plt

import keras
from keras.models import Sequential
from keras.layers import Dense, Dropout, Flatten
from keras.layers import Conv2D, MaxPooling2D
from keras.callbacks import EarlyStopping

batch_size = 10
num_classes = 2
epochs = 50
save_dir = os.path.join(os.getcwd(), 'saved_models')
model_name = 'keras_apk_trained_model.h5'

# The data, split between train and test sets
(x_train, y_train), (x_test, y_test) = common.load_dataset()
print('x_train shape:', x_train.shape)
print(x_train.shape[0], 'train samples')
print(x_test.shape[0], 'test samples')

# Convert class vectors to binary class matrices.
y_train = keras.utils.to_categorical(y_train, num_classes)
y_test = keras.utils.to_categorical(y_test, num_classes)

# Building model
model = Sequential()
model.add(Conv2D(32, (3, 3), padding='same', activation='relu',
                 input_shape=x_train.shape[1:]))
model.add(Conv2D(32, (3, 3), activation='relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.25))

model.add(Conv2D(64, (3, 3), padding='same', activation='relu'))
model.add(Conv2D(64, (3, 3), activation='relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.25))

model.add(Flatten())
model.add(Dense(256, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(num_classes, activation='softmax'))

# Training
opt = keras.optimizers.SGD(lr=0.005, decay=1e-4)
model.compile(loss='categorical_crossentropy',
              optimizer=opt,
              metrics=['accuracy'])

early_stopping = EarlyStopping(monitor='value_loss')

history = model.fit(x_train, y_train,
                    batch_size=batch_size,
                    epochs=epochs,
                    verbose=1,
                    validation_data=(x_test, y_test),
                    shuffle=True,
                    callbacks=[early_stopping]
                    )

# # Plot accuracy/loss to epochs
# # history - dict of ['acc', 'loss', 'val_acc', 'val_loss']
plt.plot(range(0, epochs), history.history['val_acc'])
plt.xlabel('Epochs')
plt.ylabel('Accuracy')
plt.show()

# plt.plot(range(0, epochs), history.history['val_loss'])
# plt.xlabel('Epochs')
# plt.ylabel('Loss')
# plt.show()

# Save model and weights
if not os.path.isdir(save_dir):
    os.makedirs(save_dir)
model_path = os.path.join(save_dir, model_name)
model.save(model_path)
print('Saved trained model at %s ' % model_path)

scores = model.evaluate(x_test, y_test, verbose=1)
print('Test loss:', scores[0])
print('Test accuracy:', scores[1])
