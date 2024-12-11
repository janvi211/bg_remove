import os
import pickle
from flask import Flask, render_template, request, redirect, url_for
import rembg
from PIL import Image

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
PICKLE_FILE = 'image_metadata.pkl'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def remove_background(input_path, output_path):
    with open(input_path, "rb") as input_file, open(output_path, "wb") as output_file:
        input_data = input_file.read()
        output_data = rembg.remove(input_data)
        output_file.write(output_data)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image_metadata(original_image, processed_image):
    metadata = {
        'original_image': original_image,
        'processed_image': processed_image
    }
    with open(PICKLE_FILE, 'wb') as f:
        pickle.dump(metadata, f)
    print(f"Metadata saved to {PICKLE_FILE}")

def load_image_metadata():
    if os.path.exists(PICKLE_FILE):
        with open(PICKLE_FILE, 'rb') as f:
            return pickle.load(f)
    return None

@app.route('/')
def index():
    metadata = load_image_metadata()
    return render_template('index.html', metadata=metadata)

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']

    if file and allowed_file(file.filename):
        filename = file.filename
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        output_path = os.path.join(UPLOAD_FOLDER, f"remove_bg_{filename}")

        remove_background(file_path, output_path)

        save_image_metadata(filename, f"remove_bg_{filename}")
        metadata = load_image_metadata()
        return render_template('index.html', original_image=filename, removed_image=f"remove_bg_{filename}",
                               metadata=metadata)

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, port=5001)
