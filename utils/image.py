from PIL import Image
from customtkinter import CTkImage

def resize_image(image_path, new_height):
    # Open an image file
    with Image.open(image_path) as img:
        # Calculate the new width maintaining the aspect ratio
        aspect_ratio = img.width / img.height
        new_width = int(new_height * aspect_ratio)
        # Resize the image
        img = img.resize((new_width, new_height), Image.ANTIALIAS)
        # Return a PhotoImage object
        return CTkImage(img)