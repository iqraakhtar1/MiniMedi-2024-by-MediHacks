import openai
from flask import Flask, request, jsonify, render_template
import os

# Initialize the Flask app
app = Flask(__name__)

# Configure OpenAI with a custom base URL and API key
openai.api_key = "API"
openai.api_base = "Use your own"  # Your custom API base URL

# Knowledge base for emergency protocols (simplified example)
protocols = {
    "cardiac arrest": "Advise the caller to begin CPR immediately and ensure someone is calling for an AED.",
    "choking": "If the person cannot breathe, advise performing the Heimlich maneuver immediately.",
    "fire": "Ensure the caller evacuates immediately and avoids smoke-filled areas."
}

# Function to process dispatcher input and provide recommendations
def get_recommendation(input_text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Your custom model
            messages=[
                {"role": "system", "content": "You are an expert emergency dispatcher assistant."},
                {"role": "user", "content": f"Based on the scenario: '{input_text}', provide evidence-based recommendations."}
            ],
            max_tokens=150
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Error in recommendation: {str(e)}"

# Route for rendering the front-end interface
@app.route('/')
def index():
    return render_template('index.html')

# Route for handling live audio transcription
@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided."}), 400

    audio_file = request.files['audio']
    audio_content = audio_file.read()

    try:
        # Use OpenAI Whisper API for transcription
        transcription = openai.Audio.transcribe(
            model="WHISPER-LARGE-V3",  # Your custom Whisper model
            file=audio_content
        )

        # Process the transcription
        transcript = transcription["text"]
        recommendation = get_recommendation(transcript)

        return jsonify({"transcript": transcript, "recommendation": recommendation})
    except Exception as e:
        return jsonify({"error": f"Audio transcription failed: {str(e)}"})

# Route for text-based prompt handling
@app.route('/prompt', methods=['POST'])
def handle_prompt():
    data = request.json
    if not data or 'input' not in data:
        return jsonify({"error": "No input text provided."}), 400

    input_text = data['input']
    recommendation = get_recommendation(input_text)

    return jsonify({"input": input_text, "recommendation": recommendation})

# Route to simulate predefined scenarios
@app.route('/simulate', methods=['GET'])
def simulate_scenario():
    scenario = request.args.get('scenario', '').lower()
    if scenario in protocols:
        return jsonify({"scenario": scenario, "recommendation": protocols[scenario]})
    else:
        return jsonify({"error": "Scenario not found."}), 404

# Run the Flask app
if __name__ == '__main__':
    # Ensure the templates folder exists for the front-end
    if not os.path.exists('templates'):
        os.makedirs('templates')

    # Create a simple front-end HTML file
    with open('templates/index.html', 'w') as f:
        f.write('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Emergency AI Dispatcher</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 600px; margin: auto; }
        textarea, input { width: 100%; margin-bottom: 10px; padding: 10px; }
        button { padding: 10px 20px; background-color: #007BFF; color: white; border: none; cursor: pointer; }
        button:hover { background-color: #0056b3; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Emergency AI Dispatcher</h1>
        <form id="promptForm">
            <textarea id="inputText" placeholder="Describe the emergency scenario..." rows="4"></textarea>
            <button type="button" onclick="submitPrompt()">Get Recommendation</button>
        </form>
        <h3>Recommendation:</h3>
        <p id="output"></p>
    </div>
    <script>
        async function submitPrompt() {
            const inputText = document.getElementById('inputText').value;
            const response = await fetch('/prompt', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ input: inputText })
            });
            const data = await response.json();
            document.getElementById('output').innerText = data.recommendation || data.error;
        }
    </script>
</body>
</html>
''')

    app.run(debug=True)
