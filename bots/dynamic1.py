import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences

# Sample conversation data
conversations = [
    (r'how are you', ['I am good, thank you!', 'I am just a bot, but I am functioning well.', 'I have no feelings, but I am here to assist.']),
    (r'what is your name', ["I'm a chatbot created by OpenAI.", 'I go by the name ChatGPT.']),
    (r'hi|hello|hey|howdy', ['Hello!', 'Hi there!', 'Hey! How can I assist you today?']),
    (r'how are you', ["'I'm just a bot", "but I'm here to help!'", "'I'm doing well. Thanks for asking!"]),
    (r'what is your name', ["I'm a customer support bot.", "You can call me ChatBot."]),
    (r'bye|goodbye', ['Goodbye!', 'Have a great day!', 'See you later. Feel free to come back anytime!']),
    (r'help', ["Sure", "I can help you with a wide range of topics.", "Just ask your question, and I'll do my best to assist."]),
    (r'what can you do', ['I can provide information, answer questions, assist with account issues, and more. Just let me know what you need.']),
    (r'account', ["For account-related issues, please provide your account ID, and I'll look into it for you."]),
    (r'order|purchase', ["If you have questions about an order or purchase, please provide your order number, and I'll check the status for you."]),
    (r'return|refund', ["For return or refund inquiries, please let me know your order details, and I'll guide you through the process."]),
    (r'shipping', ['I can help you track your shipment. Please provide your tracking number.']),
    (r'product|item', ["Tell me the product name or ID, and I'll provide you with details and availability."]),
    (r'password|reset', ['If you need to reset your password, please visit our website or use the password reset feature in the app.']),
    (r'contact', ['You can reach our customer support team at support@example.com or call our hotline at 123-456-7890.']),
    (r'feedback', ["We value your feedback! Please share your thoughts, and we'll use it to improve our services."]),
    (r'(.*)', ['I apologize', "but I'm not sure I understand your request", 'Could you please rephrase it?', "I'm here to assist you. Please ask your question again."]),
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
