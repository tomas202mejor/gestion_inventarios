import tensorflow as tf

# Cargar modelo (modifica la ruta al modelo .h5 según lo tengas)
model = tf.keras.models.load_model('predict_demand/modelo_entrenado.h5')
