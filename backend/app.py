from flask import Flask, request, jsonify
from flask_cors import CORS
from processing import get_response

app = Flask(__name__)
CORS(app)

@app.route('/get-ai-message', methods=['POST'])
def get_ai_message():
    data = request.get_json()
    input = data.get('input')
    processed_input = get_response(input)
    response = {
        "message": processed_input
    }

    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
