import numpy as np
import gzip
import pickle
import matplotlib.pyplot as plt
import math
import tensorflow as tf
from tensorflow import keras,data
from tensorflow.keras import layers,models,activations
from model_utils import *

class CNN(keras.Model):
    def __init__(self):
        super().__init__()
        self.conv1 = layers.Conv2D(32,3,padding='same',activation='relu')
        self.conv2 = layers.Conv2D(64,3,padding='same',activation='relu')
        self.conv3 = layers.Conv2D(128,3,padding='same',activation='relu')
        self.maxpool = layers.MaxPool2D(strides=2)
        self.globalpool = layers.GlobalMaxPool2D()
    def call(self,x):
        x = self.conv3(self.maxpool(self.conv2(self.maxpool(self.conv1(x)))))
        x = self.globalpool(x)
        return x

    
class CNN_GRU(layers.RNN):
    def __init__(self,cnn,op_units,ip_dims,return_sequences=True,return_state=True):
        cell = CNN_GRU_Cell(cnn,op_units,ip_dims)
        super().__init__(cell,return_sequences,return_state)
    def call (self,inputs):
        return super().call(inputs)    
    
    
class Encoder(tf.keras.Model):
    def __init__(self,cnn,ip_dims):
        super().__init__()
        self.units = ip_dims
        self.cnn_gru = CNN_GRU(cnn,self.units,ip_dims,return_sequences=True,
                               return_state=True)
    def call (self,x):
        output,state = self.cnn_gru(x)
        # output -> bs,seq_len,units
        # state -> bs,units
        return output,state


class BahdanauAttention(tf.keras.layers.Layer):
    def __init__(self, units):
        super(BahdanauAttention, self).__init__()
        self.W1 = tf.keras.layers.Dense(units)
        self.W2 = tf.keras.layers.Dense(units)
        self.V = tf.keras.layers.Dense(1)

    def call(self, query, values):
    
        # query is decoder hidden state
        # values is entire encoder hidden states
        # hidden shape == (batch_size, hidden size)
        # hidden_with_time_axis shape == (batch_size, 1, hidden size)
        hidden_with_time_axis = tf.expand_dims(query, 1)

        # score shape == (batch_size, max_length, 1)
        # we get 1 at the last axis because we are applying score to self.V
        # the shape of the tensor before applying self.V is (batch_size, max_length, units)
        score = self.V(tf.nn.tanh(
            self.W1(values) + self.W2(hidden_with_time_axis)))

        # attention_weights shape == (batch_size, seq_length, 1)
        attention_weights = tf.nn.softmax(score, axis=1)

        # context_vector shape after sum == (batch_size,1 hidden_size)
        context_vector = attention_weights * values
        context_vector = tf.reduce_sum(context_vector, axis=1, keepdims=True)

        return context_vector, attention_weights

    
class Decoder(tf.keras.Model):
    def __init__(self,units,emb_dim,seq_len,Attention,atten_units):
        # atten_units are intermediate dims for attention. 
        super().__init__()
        self.embedding = tf.keras.layers.Embedding(seq_len,emb_dim)
        self.units = units
        self.gru = tf.keras.layers.GRU(self.units,return_sequences=True,return_state=True,
                                       recurrent_initializer='glorot_uniform')
        self.attention = Attention(atten_units)
    def call(self,x,hidden,enc_output):
        x = tf.reshape(x,(-1,1))
        # x -> bs,1
        x = self.embedding(x)
        # x -> bs,emb_dim
        context,atten_w = self.attention(hidden,enc_output) 
        # context -> bs,units
        # atten_w -> bs,seq_len,1
        x = tf.concat([context,x],axis=-1)
        # x -> bs,emb_dim + units
        output,state = self.gru(x,initial_state=hidden)
        # output -> bs,1,units
        # state -> bs,units
        return tf.squeeze(output), state, atten_w
    

class Full_Model(tf.keras.Model):
    def __init__(self,CNN,Encoder,Decoder,Attention,emb_dim=5,seq_len=5,atten_units=25,final_rep=10):
        """ Arguments
            CNN -> CNN Class
            Encoder -> Encoder Class
            Decoder -> Decoder Class
            Attention -> Attention Class
            emb_dim -> embedding dimension at decoder
            seq_len -> sequence length
            atten_units -> hidden dims for Attention
            final_rep -> final output shape

            Returns
            final_op -> final ouput (bs,output_seq,final_rep)
            all_atten -> attention (bs,output_seq,seq_len,1)  

        """
        super().__init__()
        self.cnn = CNN()
        ip_dims = self.cnn.compute_output_shape((None,None,None,1))[-1]
        self.encoder = Encoder(self.cnn,ip_dims)
        self.decoder = Decoder(ip_dims,emb_dim,seq_len,Attention,atten_units)
        self.seq_len = seq_len
        self.fc = tf.keras.layers.Dense(final_rep)
    def call(self,x,labels):
        bs = x.shape[0]
        seq_input = tf.convert_to_tensor(np.tile(np.array([0,1,2,3,4]),(bs,1)))
        enc_output,enc_hidden = self.encoder(x)
        # enc_output -> bs,seq_len,units
        # enc_hidden -> bs,units
        dec_hidden = enc_hidden
        final_op,all_atten = [],[]
        for i in range(self.seq_len):
            dec_output,dec_hidden,atten_w = self.decoder(seq_input[:,i],dec_hidden,enc_output)
            # dec_output = bs,units
            # dec_hiddem = bs,units
            # atten_w = bs,seq_len,1
            final_op.append(dec_output)
            all_atten.append(atten_w)
        final_op = tf.transpose(tf.convert_to_tensor(final_op),perm=(1,0,2))
        final_op = self.fc(final_op)
        all_atten = tf.transpose(tf.convert_to_tensor(all_atten),perm=(1,0,2,3))
        return final_op,all_atten