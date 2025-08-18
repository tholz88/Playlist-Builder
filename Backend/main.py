from flask import Flask, request, jsonify

app = Flask(__name__)

# Speicher für den Text
stored_text = ""

@app.route('/text', methods=['POST'])
def post_text():
    global stored_text
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "Bitte 'text' im JSON senden"}), 400
    stored_text = data['text']
    return jsonify({"message": "Text gespeichert"}), 201

@app.route('/text', methods=['GET'])
def get_text():
    return jsonify({"text": stored_text})

if __name__ == '__main__':
    app.run(debug=True)