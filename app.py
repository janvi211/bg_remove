from flask import Flask, render_template, request, redirect, url_for
import os
import rembg
from PIL import Image
import logging

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

MAX_IMAGE_SIZE = (1024, 1024)

# Set up logging
logging.basicConfig(level=logging.INFO)

def resize_image(image_path):
    """Resize image to fit within the max dimensions."""
    with Image.open(image_path) as img:
        img.thumbnail(MAX_IMAGE_SIZE)
        img.save(image_path)  # Save the resized image back to the same path
    return image_path

def remove_background(input_path, output_path):
    """Remove background from image using rembg."""
    try:
        with open(input_path, "rb") as input_file, open(output_path, "wb") as output_file:
            input_data = input_file.read()
            output_data = rembg.remove(input_data)
            output_file.write(output_data)
    except Exception as e:
        logging.error(f"Error removing background: {e}")
        raise e

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def download_model_if_needed():
    """Check if the model exists; if not, download it."""
    model_path = '/opt/render/.u2net/u2net.onnx'  # Change if needed
    if not os.path.exists(model_path):
        logging.info("Downloading the u2net model...")
        # Download the model file from the rembg GitHub repository
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        os.system(f"curl -L -o {model_path} https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx")
    return model_path

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/', methods=['POST'])
def upload_image():
    """Handle image upload and background removal."""
    if 'file' not in request.files:
        logging.warning("No file part in the request")
        return redirect(request.url)
    
    file = request.files['file']
    
    if file and allowed_file(file.filename):
        filename = file.filename
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        # Resize the image before processing
        resize_image(file_path)
        
        # Path for the output image with removed background
        output_path = os.path.join(UPLOAD_FOLDER, f"remove_bg_{filename}")
        
        try:
            # Ensure model is available
            download_model_if_needed()
            
            # Remove the background from the image
            remove_background(file_path, output_path)
            
            original_image = filename
            removed_background_image = f"remove_bg_{filename}"
            
            # Return the images for display
            return render_template('index.html', original_image=original_image, removed_image=removed_background_image)
        
        except Exception as e:
            logging.error(f"Error processing the image: {e}")
            return render_template('index.html', error="There was an error processing the image.")
    
    logging.warning("Invalid file type uploaded.")
    return render_template('index.html', error="Invalid file type. Please upload a valid image.")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(debug=True, host='0.0.0.0', port=port)
