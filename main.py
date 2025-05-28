from flask import Flask, request, send_file, jsonify
import os
import ffmpeg
import uuid

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/process-video', methods=['POST'])
def process_video():
    if 'video' not in request.files or 'audio' not in request.files:
        return jsonify({'error': 'Both video and audio files are required'}), 400

    video_file = request.files['video']
    audio_file = request.files['audio']

    # Save files with unique names
    video_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}.mp4")
    audio_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}.mp3")
    output_path = os.path.join(OUTPUT_FOLDER, f"{uuid.uuid4()}.mp4")

    video_file.save(video_path)
    audio_file.save(audio_path)

    try:
        # Process video: add audio, crop to 9:16 (center), trim to audio length
        video_stream = ffmpeg.input(video_path)
        audio_stream = ffmpeg.input(audio_path)
        (
            ffmpeg
            .output(
                video_stream,
                audio_stream,
                output_path,
                map=['0:v', '1:0'],
                shortest=None,
                vf='crop=in_h*9/16:in_h'
            )
            .overwrite_output()
            .run()
        )

        return send_file(output_path, as_attachment=True)

    except ffmpeg.Error as e:
        return jsonify({'error': e.stderr.decode()}), 500

    finally:
        # Clean up uploaded files
        for f in [video_path, audio_path]:
            if os.path.exists(f):
                os.remove(f)

@app.route('/')
def hello_world():
    return 'Hello, World!'

if __name__ == '__main__':
    app.run(debug=True, port=10000)
