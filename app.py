from flask import Flask, render_template, request, send_from_directory
from PIL import Image, ImageDraw, ImageFont
import io, os, zipfile, datetime

# Explicit folders
templates = 'templates'
static = 'static'
app = Flask(__name__, template_folder=templates, static_folder=static)

# Output directory
OUTPUT_DIR = os.path.join(app.static_folder, 'outputs')
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Convert image to ASCII string (width 200 columns)
def image_to_ascii(image, width=200):
    aspect_ratio = image.height / image.width
    new_height = int(aspect_ratio * width * 0.55)
    image = image.convert('L').resize((width, new_height))
    pixels = image.getdata()
    chars = "@%#*+=-:. "  # 10 levels of shading
    # Map pixel (0-255) to index (0-9)
    new_pixels = [chars[pixel * len(chars) // 256] for pixel in pixels]
    return "\n".join(
        "".join(new_pixels[i:i+width])
        for i in range(0, len(new_pixels), width)
    )

# Render ASCII as image for JPEG download
def ascii_to_image(ascii_str, bg_color="black", font_color="green"):
    lines = ascii_str.split("\n")
    font = ImageFont.load_default()
    # Use temporary draw to measure text size
    temp_img = Image.new('RGB', (1, 1))
    draw_temp = ImageDraw.Draw(temp_img)
    # Calculate max text width per line
    widths = [draw_temp.textbbox((0, 0), line, font=font)[2] for line in lines]
    max_width = max(widths) if widths else 0
    # Calculate line height using textbbox
    bbox = draw_temp.textbbox((0, 0), 'A', font=font)
    line_height = bbox[3] - bbox[1]
    # Create final image
    img = Image.new('RGB', (max_width, line_height * len(lines)), color=bg_color)
    draw = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        draw.text((0, i * line_height), line, fill=font_color, font=font)
    return img

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['image']
        if file:
            image = Image.open(io.BytesIO(file.read()))
            ascii_art = image_to_ascii(image)

            # Save ASCII as text
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            txt_filename = f"ascii_{timestamp}.txt"
            txt_path = os.path.join(OUTPUT_DIR, txt_filename)
            with open(txt_path, 'w') as f:
                f.write(ascii_art)

            # Save ASCII as JPEG
            img = ascii_to_image(ascii_art)
            img_filename = f"ascii_{timestamp}.jpg"
            img_path = os.path.join(OUTPUT_DIR, img_filename)
            img.save(img_path, 'JPEG')

            # Bundle both into ZIP
            zip_filename = f"ascii_{timestamp}.zip"
            zip_path = os.path.join(OUTPUT_DIR, zip_filename)
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                zipf.write(txt_path, txt_filename)
                zipf.write(img_path, img_filename)

            return render_template(
                'result.html', ascii_art=ascii_art,
                txt_file=txt_filename,
                img_file=img_filename,
                zip_file=zip_filename
            )
    return render_template('index.html')

# Serve downloads
@app.route('/download/<path:filename>')
def download(filename):
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
