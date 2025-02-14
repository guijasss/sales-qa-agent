from flask import Flask, request, jsonify
from ollama import chat, ChatResponse
from re import sub, DOTALL

# Initialize Flask app
app = Flask(__name__)

# Function to query the DeepSeek model through Ollama
def ask_deepseek_model(question):
    try:
        # Query the DeepSeek model using Ollama
        response = chat(model="deepseek-r1:1.5b", messages=[{"role": "user", "content": question}]).message.content
        return sub(r'<think>.*?</think>', '', response, flags=DOTALL).strip()
    
    except Exception as e:
        return f"Error: {str(e)}"

# Define the route for answering questions
@app.route('/ask', methods=['GET'])
def ask_question():
    # Get the question from the POST request
    data = request.get_json()
    question = data.get('question', '')

    if not question:
        return jsonify({"error": "No question provided"}), 400

    # Get the answer from DeepSeek
    answer = ask_deepseek_model(question)
    
    # Return the answer in JSON format
    return jsonify({"question": question, "answer": answer})

if __name__ == '__main__':
    # Run the Flask web server locally
    app.run(host='0.0.0.0', port=5000)
