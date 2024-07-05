import cv2
import numpy as np
import os
from flask import Flask, request, render_template, send_file

app = Flask(__name__)

# Ensure the 'uploads' directory exists
if not os.path.exists('uploads'):
    os.makedirs('uploads')

# Encryption function
def encrypt(img1_path, img2_path, output_path):
    # Read the images
    img1 = cv2.imread(img1_path)
    img2 = cv2.imread(img2_path)

    if img1 is None or img2 is None:
        raise ValueError("One of the images could not be read. Please check the file paths.")

    # Resize the second image to match the first image's dimensions
    img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

    # Iterate over each pixel
    for i in range(img2.shape[0]):
        for j in range(img2.shape[1]):
            for l in range(3):
                # Convert pixel values to 8-bit binary strings
                v1 = format(img1[i][j][l], '08b')
                v2 = format(img2[i][j][l], '08b')
                # Hide the 4 most significant bits of v2 in the 4 least significant bits of v1
                v3 = v1[:4] + v2[:4]
                # Update the pixel value in img1
                img1[i][j][l] = int(v3, 2)

    # Save the encrypted image
    cv2.imwrite(output_path, img1)

# Decryption function
def decrypt(img_path, output_path1, output_path2):
    # Read the encrypted image
    img = cv2.imread(img_path)
    width, height, _ = img.shape
    img1 = np.zeros((width, height, 3), np.uint8)
    img2 = np.zeros((width, height, 3), np.uint8)

    # Iterate over each pixel
    for i in range(width):
        for j in range(height):
            for l in range(3):
                # Extract the 4 MSBs to reconstruct the carrier image
                # and 4 LSBs to reconstruct the hidden image
                v1 = format(img[i][j][l], '08b')
                v2 = v1[:4] + '0000'
                v3 = v1[4:] + '0000'
                img1[i][j][l] = int(v2, 2)
                img2[i][j][l] = int(v3, 2)

    # Save the decrypted images
    cv2.imwrite(output_path1, img1)
    cv2.imwrite(output_path2, img2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file1' not in request.files or 'file2' not in request.files:
        return 'No file part'

    file1 = request.files['file1']
    file2 = request.files['file2']

    if file1.filename == '' or file2.filename == '':
        return 'No selected file'

    file1_path = os.path.join('uploads', file1.filename)
    file2_path = os.path.join('uploads', file2.filename)
    file1.save(file1_path)
    file2.save(file2_path)

    encrypted_path = os.path.join('uploads', 'encrypted.png')
    encrypt(file1_path, file2_path, encrypted_path)

    return send_file(encrypted_path, as_attachment=True)

@app.route('/decrypt', methods=['POST'])
def decrypt_image():
    if 'file' not in request.files:
        return 'No file part'

    file = request.files['file']

    if file.filename == '':
        return 'No selected file'

    file_path = os.path.join('uploads', file.filename)
    file.save(file_path)

    decrypted_path1 = os.path.join('uploads', 'decrypted1.png')
    decrypted_path2 = os.path.join('uploads', 'decrypted2.png')
    decrypt(file_path, decrypted_path1, decrypted_path2)

    # Return the two decrypted images as a ZIP file
    from zipfile import ZipFile

    zip_path = os.path.join('uploads', 'decrypted_images.zip')
    with ZipFile(zip_path, 'w') as zipf:
        zipf.write(decrypted_path1, os.path.basename(decrypted_path1))
        zipf.write(decrypted_path2, os.path.basename(decrypted_path2))

    return send_file(zip_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
