import nltk 
from nltk.chat.util import Chat, reflections
import random

# Define patterns and responses for the chatbot
patterns = [
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

# Create a chatbot
chatbot = Chat(patterns, reflections)

# Function to start the chat
def start_chat():
    print("Hello! I'm your chatbot. How can I assist you today?")
    chatbot.converse()

# Start the chat
if __name__ == "__main__":
    start_chat()
