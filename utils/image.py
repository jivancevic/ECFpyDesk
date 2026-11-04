from PIL import Image
from customtkinter import CTkImage

# Pillow 10 removed Image.ANTIALIAS in favor of Image.Resampling.LANCZOS.
# Resolve a cross-version resampling filter that works on Pillow 8/9/10+.
try:
    RESAMPLE_FILTER = Image.Resampling.LANCZOS
except AttributeError:
    RESAMPLE_FILTER = Image.LANCZOS if hasattr(Image, "LANCZOS") else Image.BICUBIC

def resize_image(image_path, new_height):
    # Open an image file
    with Image.open(image_path) as img:
        # Calculate the new width maintaining the aspect ratio
        aspect_ratio = img.width / img.height
        new_width = int(new_height * aspect_ratio)
        # Resize the image using a version-compatible resampling filter
        img = img.resize((new_width, new_height), RESAMPLE_FILTER)
        # Return a PhotoImage object
        return CTkImage(img)