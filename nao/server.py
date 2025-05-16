# combined_server.py
from flask import Flask, request, jsonify
import speech_recognition as sr
 
import pickle
 
import tensorflow as tf
from keras.models import load_model
 
import numpy as np
 
def load_array(load_path):
    with open(load_path, 'rb') as file:
        return pickle.load(file)
    
x_train = load_array('x_train.pkl')
model = load_model("first_try.keras")
 
# Parameters
vocab_size = 20000  # Maximum number of unique tokens
max_length = 250    # Maximum length of sequences after padding
 
# Initialize TextVectorization layer
vectorize_layer = tf.keras.layers.TextVectorization(
    max_tokens=vocab_size,
    output_mode='int',
    output_sequence_length=max_length
)
 
# Prepare the layer with the training data
# 'x_train' should be a dataset or a list/array of strings
vectorize_layer.adapt(x_train)
 
app = Flask(__name__)
 
def speech_to_text(wav_file_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_file_path) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data)
            print(f"Transcribed Speech: {text}")
            return text
        except sr.UnknownValueError:
            print("Speech Recognition could not understand the audio.")
            return "Sorry, I couldn't understand the audio."
        except sr.RequestError:
            print("Error with the Speech-to-Text service.")
            return "Error with the Speech-to-Text service."
 
@app.route('/chat', methods=['POST'])
def chat_with_robot():
    # Handle both audio and text JSON
    if 'audio' in request.files:
        # Speech input
        audio_file = request.files['audio']
        wav_file_path = 'temp_audio.wav'
        audio_file.save(wav_file_path)
        user_message = speech_to_text(wav_file_path)
    else:
        # JSON text input
        user_message = request.json.get("message", "").strip()
 
    vect_message = vectorize_layer(user_message)
    score = model.predict(np.expand_dims(vect_message, axis=0))
 
    return jsonify({'score': str(score[0][0])})
 
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)