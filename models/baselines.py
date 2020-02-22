import tensorflow as tf
from numpy import moveaxis
from numpy import asarray
from tensorflow.keras import layers


class DummyModel(tf.keras.Model):
    def __init__(self):
        super(DummyModel, self).__init__()
        self.flatten = layers.Flatten()
        self.dense1 = layers.Dense(32, activation=tf.nn.relu)
        self.dense2 = layers.Dense(1, activation=None)
        
    def call(self, inputs):
        x = self.dense1(self.flatten(inputs))
        return self.dense2(x)

class SunsetModel(tf.keras.Model):
    def __init__(self):
        super(SunsetModel, self).__init__()
        self.conv1 = layers.Conv2D(12, (3, 3), activation='relu', padding='same')
        self.conv2 = layers.Conv2D(24, (3, 3), activation='relu', padding='same')
        self.batch_norm = layers.BatchNormalization()
        self.maxpooling = layers.MaxPool2D(pool_size=(2, 2))
        self.flatten = layers.Flatten()
        self.dense1 = layers.Dense(1024, activation=tf.nn.relu)
        self.dense2 = layers.Dense(1024, activation=tf.nn.relu)
        self.dense3 = layers.Dense(1, activation=None)

    def call(self, inputs):
        # Conv block 1
        x = self.conv1(inputs)
        #x = self.batch_norm(x)
        x = self.maxpooling(x)
        
        # Conv block 2
        x = self.conv2(x)
        #x = self.batch_norm(x)
        x = self.maxpooling(x)
        
        # Fully connected
        x = self.flatten(x)
        x = self.dense1(x)
        x = self.dense2(x)
        x = self.dense3(x)
        return x

class Sunset3DModel(tf.keras.Model):
    def __init__(self):
        super(Sunset3DModel, self).__init__()
        self.conv1 = layers.Conv3D(12, (3, 3, 3), activation='relu', padding='same')
        self.conv2 = layers.Conv3D(24, (3, 3, 3), activation='relu', padding='same')
        self.maxpooling = layers.MaxPool3D(pool_size=(2, 2, 2))
        self.flatten = layers.Flatten()
        self.dense1 = layers.Dense(1024, activation=tf.nn.relu)
        self.dense2 = layers.Dense(1024, activation=tf.nn.relu)
        self.dense3 = layers.Dense(4, activation=None)

    def call(self, inputs):
         # Conv block 1
        x = self.conv1(inputs)
        #x = self.batch_norm(x)
        x = self.maxpooling(x)
        
        # Conv block 2
        x = self.conv2(x)
        #x = self.batch_norm(x)
        x = self.maxpooling(x)
        
        # Fully connected
        x = self.flatten(x)
        x = self.dense1(x)
        x = self.dense2(x)
        x = self.dense3(x)
        return x
    
class ConvDemModel(tf.keras.Model):
    def __init__(self, image_size):
        super(ConvDemModel, self).__init__()
        self.conv1 = layers.Conv2D(32, (3, 3), activation='relu', padding='same')
        self.conv2 = layers.Conv2D(64, (3, 3), activation='relu', padding='same')
        self.conv3 = layers.Conv2D(64, (3, 3), activation='relu', padding='same')
        self.maxpooling = layers.MaxPool2D(pool_size=(2, 2))
        self.flatten = layers.Flatten()
        self.droppedout = layers.Dropout(0.2)
        self.dense = layers.Dense(1, activation=None)

    def call(self, inputs):
        # Conv block 1:        
        x = self.conv1(inputs)   # 30x30x5 input convs to 30x30x32
        x = self.maxpooling(x)   # 30x30x32 maxpools to 15x15x32

        # Conv block 2
        x = self.conv2(x)        # 15x15x32 convs to 15x15x32
        x = self.maxpooling(x)   # 15x15x32 maxpools to 7x7x64
        
        # Conv block 3        
        x = self.conv3(x)        # 7x7x64 convs to 7x7x64
        x = self.maxpooling(x)   # 7x7x64 maxpools to 3x3x64
        
        # Conv block 4        
        x = self.conv3(x)        # 3x3x64 convs to 3x3x64        

        # Flatten, dropped out (%20) & output
        x = self.flatten(x)      
        x = self.droppedout(x)
        x = self.dense(x)

        return x

class ConvLSTM(tf.keras.Model):
    def __init__(self):
        super(ConvLSTM, self).__init__()
        self.average_pool = layers.TimeDistributed(layers.AveragePooling2D(pool_size=(4, 4)))
        self.conv1 = layers.ConvLSTM2D(128, (5, 5), return_sequences = True)
        self.conv2 = layers.ConvLSTM2D(64, (5, 5), return_sequences = True)
        self.conv3 = layers.ConvLSTM2D(64, (5, 5))
        self.flatten = layers.Flatten()
        self.dense1 = layers.Dense(1024, activation=tf.nn.relu)
        self.dense2 = layers.Dense(1024, activation=tf.nn.relu)
        self.dense3 = layers.Dense(4, activation=None)
    
    def call(self, inputs):
        # print('intput shape : ', inputs.shape)
        x = self.average_pool(inputs)
        # print('after avg pooling : ', x.shape)
        x = self.conv1(inputs)
        # print('after conv1 : ', x.shape)
        x = self.conv2(x)
        #print('after conv2 : ', x.shape)
        x = self.conv3(x)
        #print('after conv23 : ', x.shape)
        x = self.flatten(x)
        #print('after flatten : ', x.shape)
        x = self.dense1(x)
        x = self.dense2(x)
        x = self.dense3(x)
        return x

