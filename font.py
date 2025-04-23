from PIL import Image, ImageDraw, ImageFont
import shutil
import os
import time

def render_text_to_unicode(text, font_path, font_size=20, scale=1):
    # Load font
    font = ImageFont.truetype(font_path, font_size)
    bbox = font.getbbox(text)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]

    # Render text to image
    image = Image.new("L", (w + 10, h + 10), color=255)
    draw = ImageDraw.Draw(image)
    draw.text((5, 5), text, font=font, fill=0)

    # Resize for terminal display
    image = image.resize((int(image.width * scale), int(image.height * scale * 0.5)))
    pixels = image.load()

    # Convert image to Unicode blocks
    result = ""
    for y in range(image.height):
        line = ""
        for x in range(image.width):
            brightness = pixels[x, y]
            if brightness < 50:
                line += "█"
            elif brightness < 100:
                line += "▓"
            elif brightness < 150:
                line += "▒"
            elif brightness < 200:
                line += "░"
            else:
                line += " "
        result += line.rstrip() + "\n"
    return result

def display_top_right(unicode_art):
    term_width = shutil.get_terminal_size().columns
    lines = unicode_art.splitlines()
    for line in lines:
        pad = term_width - len(line)
        print(" " * max(pad, 0) + line)

if __name__ == "__main__":
    FONT_PATH = "C:\\Windows\\Fonts\\arialbd.ttf"  # Windows bold font path or use a different font
    count = 1
    
    try:
        while True:
            os.system("cls" if os.name == "nt" else "clear")  # Clear terminal screen
            
            # Render the current count to Unicode art
            text = str(count)
            art = render_text_to_unicode(text, FONT_PATH, font_size=20, scale=1)
            
            # Display the current count at top-right of terminal
            display_top_right(art)
            
            # Increment the count
            count += 1
            
            # Wait a little before updating (optional)
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\nCounting stopped by user.")
