from flask import Flask, render_template_string, request, jsonify
from googletrans import Translator
import speech_recognition as sr
import io
import base64

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Speech Translation App</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #e7f1ff; margin: 0; padding: 0; display: flex; flex-direction: column; align-items: center; }
        .title { text-align: center; background-color: #ff0000; padding: 20px; border-radius: 10px; color: #FFD700; font-size: 48px; font-weight: bold; margin-top: 20px; width: 80%; border: 5px solid #ff0000; }
        .subtitle { text-align: center; color: #ffcc00; font-size: 36px; font-weight: bold; margin: 10px 0; text-shadow: 1px 1px 2px #000; }
        .container { background-color: #d0e7ff; padding: 20px; border-radius: 10px; width: 80%; max-width: 800px; box-shadow: 0 0 10px rgba(0,0,0,0.1); margin-top: 20px; display: flex; justify-content: space-between; }
        .user { flex: 1; margin: 10px; background-color: #7b68ee; padding: 15px; border-radius: 10px; min-width: 300px; max-width: 400px; }
        h3 { color: #ffcc00; font-size: 28px; text-align: center; text-shadow: 1px 1px 2px #000; }
        select, button, textarea { width: 100%; padding: 10px; margin: 10px 0; border-radius: 5px; border: 1px solid #ccc; font-size: 16px; box-sizing: border-box; }
        button { background-color: #FFD700; color: #000; cursor: pointer; transition: background-color 0.3s; border: none; }
        button:hover { background-color: #FFC300; }
        .output-box { background-color: #f9f9f9; padding: 15px; border-radius: 5px; border: 1px solid #ccc; margin-top: 20px; word-wrap: break-word; }
        #status { color: #333; margin-top: 10px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="title">Gungun sharma </div>
    <div class="subtitle">🌍 Language Translator 🌍</div>
    <div class="container">
        <div class="user">
            <h3>User 1</h3>
            <select id="source_language_1">{% for language, code in languages.items() %}<option value="{{ code }}">{{ language }}</option>{% endfor %}</select>
            <select id="target_language_1">{% for language, code in languages.items() %}<option value="{{ code }}">{{ language }}</option>{% endfor %}</select>
            <textarea id="input_text_1" rows="4" placeholder="Enter text or click 'Start Listening' to speak"></textarea>
            <div>
                <button onclick="startListening(1)">Start Listening 🎤</button>
                <button onclick="translateText(1)">Translate Text</button>
            </div>
            <div id="status_1"></div>
            <div id="transcription_1" class="output-box" style="display: none;"></div>
            <div id="translation_1" class="output-box" style="display: none;"></div>
        </div>
        <div class="user">
            <h3>User 2</h3>
            <select id="source_language_2">{% for language, code in languages.items() %}<option value="{{ code }}">{{ language }}</option>{% endfor %}</select>
            <select id="target_language_2">{% for language, code in languages.items() %}<option value="{{ code }}">{{ language }}</option>{% endfor %}</select>
            <textarea id="input_text_2" rows="4" placeholder="Enter text or click 'Start Listening' to speak"></textarea>
            <div>
                <button onclick="startListening(2)">Start Listening 🎤</button>
                <button onclick="translateText(2)">Translate Text</button>
            </div>
            <div id="status_2"></div>
            <div id="transcription_2" class="output-box" style="display: none;"></div>
            <div id="translation_2" class="output-box" style="display: none;"></div>
        </div>
    </div>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script>
        let audioContext;
        let recorder;

        async function startListening(user) {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                audioContext = new (window.AudioContext || window.webkitAudioContext)();
                const source = audioContext.createMediaStreamSource(stream);
                recorder = new Recorder(source);

                recorder.record();
                $(`#status_${user}`).text('Listening... Speak now (5 seconds)');

                setTimeout(() => {
                    stopListening(user);
                }, 5000);
            } catch (err) {
                console.error('Error accessing microphone:', err);
                alert('Error accessing microphone. Please make sure you have given permission to use the microphone.');
            }
        }

        function stopListening(user) {
            recorder.stop();
            $(`#status_${user}`).text('Processing...');

            recorder.exportWAV((blob) => {
                sendAudioToServer(blob, user);
            });
        }

        function sendAudioToServer(audioBlob, user) {
            const reader = new FileReader();
            reader.onloadend = () => {
                const base64Audio = reader.result.split(',')[1];
                $.ajax({
                    url: '/listen',
                    type: 'POST',
                    data: {
                        audio: base64Audio,
                        source_language: $(`#source_language_${user}`).val(),
                        target_language: $(`#target_language_${user}`).val(),
                        user: user
                    },
                    success: function(response) {
                        $(`#status_${user}`).text('');
                        if (response.error) {
                            alert(response.error);
                        } else {
                            $(`#input_text_${user}`).val(response.transcription);
                            $(`#transcription_${user}`).text('Original: ' + response.transcription).show();
                            $(`#translation_${user}`).text('Translation: ' + response.translation).show();
                        }
                    },
                    error: function() {
                        $(`#status_${user}`).text('');
                        alert('An error occurred while processing your request.');
                    }
                });
            };
            reader.readAsDataURL(audioBlob);
        }

        function translateText(user) {
            $(`#status_${user}`).text('Translating...');
            $.ajax({
                url: '/translate',
                type: 'POST',
                data: {
                    source_language: $(`#source_language_${user}`).val(),
                    target_language: $(`#target_language_${user}`).val(),
                    text: $(`#input_text_${user}`).val()
                },
                success: function(response) {
                    $(`#status_${user}`).text('');
                    if (response.error) {
                        alert(response.error);
                    } else {
                        $(`#transcription_${user}`).text('Original: ' + response.original).show();
                        $(`#translation_${user}`).text('Translation: ' + response.translation).show();
                    }
                },
                error: function() {
                    $(`#status_${user}`).text('');
                    alert('An error occurred while processing your request.');
                }
            });
        }
    </script>
    <script src="https://cdn.rawgit.com/mattdiamond/Recorderjs/08e7abd9/dist/recorder.js"></script>
</body>
</html>
"""

@app.route('/')
def index():
    languages = {
        'Hindi': 'hi',
        'Bengali': 'bn',
        'Telugu': 'te',
        'Marathi': 'mr',
        'Tamil': 'ta',
        'Gujarati': 'gu',
        'Punjabi': 'pa',
        'Malayalam': 'ml',
        'Urdu': 'ur',
        'English': 'en',
        'Spanish': 'es'
    }
    return render_template_string(HTML_TEMPLATE, languages=languages)

@app.route('/listen', methods=['POST'])
def listen():
    audio_data = base64.b64decode(request.form['audio'])
    source_language = request.form['source_language']
    target_language = request.form['target_language']
    
    recognizer = sr.Recognizer()
    
    with io.BytesIO(audio_data) as audio_file:
        with sr.AudioFile(audio_file) as source:
            audio = recognizer.record(source)
    
    try:
        transcription = recognizer.recognize_google(audio, language=source_language)
        translator = Translator()
        translation = translator.translate(transcription, src=source_language, dest=target_language)
        return jsonify(transcription=transcription, translation=translation.text)
    except sr.UnknownValueError:
        return jsonify(error="Could not understand audio"), 400
    except sr.RequestError:
        return jsonify(error="Could not request results from Google Speech Recognition service"), 400

@app.route('/translate', methods=['POST'])
def translate():
    source_language = request.form['source_language']
    target_language = request.form['target_language']
    text = request.form['text']
    
    translator = Translator()
    translation = translator.translate(text, src=source_language, dest=target_language)
    return jsonify(original=text, translation=translation.text)

if __name__ == '__main__':
    app.run(debug=True)