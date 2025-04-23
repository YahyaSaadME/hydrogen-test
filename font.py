from PIL import Image, ImageDraw, ImageFont

# Define text and smaller font size
text = "HELLO"
font_size = 30  # Reduced font size
font_path = "Lexend-Regular.ttf"  # Ensure this is the correct path to the Lexend font

# Load the font
font = ImageFont.truetype(font_path, font_size)

# Create an image for the text with a white background
image = Image.new("L", (300, 60), color=255)  # Adjust width and height as needed
draw = ImageDraw.Draw(image)
draw.text((10, 10), text, font=font, fill=0)

# Convert the image to pixels and print as ASCII
pixels = image.load()
for y in range(image.height):
    line = ""
    for x in range(image.width):
        if pixels[x, y] < 128:  # Dark pixel (text area)
            line += "█"
        else:
            line += " "  # Light pixel (background area)
    print(line)
