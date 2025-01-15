from flask import Flask, request
from pyngrok import ngrok
from datetime import datetime

app = Flask(__name__)
app.recordings = []

print("\n=== Starting Application ===\n")

@app.route('/recording-status', methods=['POST'])
def recording_status():
    print("\n=== Webhook Received! ===")
    print("Form data:", dict(request.form))
    
    recording_data = {
        'sid': request.form.get('RecordingSid'),
        'url': f"{request.form.get('RecordingUrl')}.mp3" if request.form.get('RecordingUrl') else None,
        'status': request.form.get('RecordingStatus'),
        'duration': request.form.get('RecordingDuration'),
        'received_at': str(datetime.now())
    }
    
    print("Recording data:", recording_data)
    app.recordings.append(recording_data)
    return 'OK', 200

@app.route('/test', methods=['GET'])
def test():
    print("\n=== Test Endpoint Hit! ===")
    print("Headers:", dict(request.headers))
    print("Remote addr:", request.remote_addr)
    return "Test endpoint working!"

@app.route('/recordings', methods=['GET'])
def list_recordings():
    print("\n=== Viewing Recordings ===")
    print("Total recordings:", len(app.recordings))
    
    html = "<h1>Recordings</h1>"
    html += f"<p>Total recordings: {len(app.recordings)}</p>"
    html += "<ul>"
    for recording in app.recordings:
        html += f"<li>SID: {recording['sid']}<br>"
        html += f"URL: <a href='{recording['url']}' target='_blank'>{recording['url']}</a><br>"
        html += f"Status: {recording['status']}<br>"
        html += f"Duration: {recording['duration']} seconds<br>"
        html += f"Received: {recording['received_at']}</li><br><br>"
    html += "</ul>"
    return html

def start_ngrok():
    public_url = ngrok.connect(5001).public_url
    print("\n=== NGROK URL ===")
    print(f"Public URL: {public_url}")
    print("\n=== USE THIS IN YOUR TWIML BIN ===")
    print(f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Record recordingStatusCallback="{public_url}/recording-status"/>
    <Dial>{{{{To}}}}</Dial>
</Response>""")
    return public_url

if __name__ == '__main__':
    print("\n=== Starting Server ===")
    ngrok_url = start_ngrok()
    # Run the Flask app on all interfaces
    app.run(host='0.0.0.0', port=5001)
