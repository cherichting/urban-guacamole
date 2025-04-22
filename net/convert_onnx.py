from keras.models import load_model
import tensorflow as tf
from tensorflow.python.keras import backend as K
import keras2onnx,onnx
sess = tf.compat.v1.Session()
graph = tf.compat.v1.get_default_graph()
K.set_session(sess)
model = load_model("logs/ep100-loss0.089-val_loss0.47.h5", compile=False)  ## 载入人脸特征提取神经网络

onnx_model = keras2onnx.convert_keras(model, model.name)
onnx.save_model(onnx_model, "model.onnx")
# keras2onnx.save_model("model.onnx", model)

# tf.saved_model.save(model, "tmp_model")
