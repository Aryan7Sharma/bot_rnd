import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences

# Sample conversation data
conversations = [
    ("hi", "Hello! How can I help you?"),
    ("What's the weather today?", "I'm not sure. Let me check..."),
    ("It's sunny outside.", "Great! Enjoy the sunshine."),
    ("bye", "Goodbye! Have a nice day."),
]


# Separate user inputs and bot responses
user_inputs, bot_responses = zip(*conversations)

# Initialize and fit a tokenizer
tokenizer = Tokenizer()
tokenizer.fit_on_texts(user_inputs + bot_responses)

# Convert text to sequences
user_sequences = tokenizer.texts_to_sequences(user_inputs)
bot_sequences = tokenizer.texts_to_sequences(bot_responses)

# Pad sequences to the same length
user_sequences = pad_sequences(user_sequences, padding='post')
bot_sequences = pad_sequences(bot_sequences, padding='post')

# Define a simple sequence-to-sequence model
# Define a simple sequence-to-sequence model
model = keras.Sequential([
    keras.layers.Embedding(input_dim=len(tokenizer.word_index) + 1, output_dim=64),
    keras.layers.LSTM(64),
    keras.layers.RepeatVector(bot_sequences.shape[1]),  # Use bot_sequences.shape[1] as the argument
    keras.layers.LSTM(64, return_sequences=True),
    keras.layers.TimeDistributed(keras.layers.Dense(len(tokenizer.word_index) + 1, activation='softmax'))
])



# Compile the model
model.compile(optimizer='adam', loss='sparse_categorical_crossentropy')

# Train the model (you would need a more extensive dataset for better performance)
model.fit(user_sequences, np.expand_dims(bot_sequences, -1), epochs=50, verbose=2)

# Function to generate responses
def generate_response(user_input):
    user_sequence = tokenizer.texts_to_sequences([user_input])
    user_sequence = pad_sequences(user_sequence, maxlen=user_sequences.shape[1], padding='post')
    bot_sequence = model.predict(user_sequence)
    bot_sequence = np.argmax(bot_sequence, axis=-1)[0]
    bot_response = ' '.join([tokenizer.index_word[i] for i in bot_sequence if i > 0])
    return bot_response

# Chat loop
while True:
    user_input = input("You: ")
    if user_input.lower() == 'exit':
        break
    bot_response = generate_response(user_input)
    print("Bot:", bot_response)
