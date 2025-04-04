from PIL import Image
import os

"""
If you would like to make renders of env make sure to call after env.render():

screenshot = pygame.display.get_surface()  # Get the current screen surface
pygame.image.save(screenshot, f"../<FILE_PATH>.png")  # Save it as a PNG file
"""

# Parameters
image_folder = '../../dev/'  # Folder containing PNG images
output_gif = '../../media/simulation.gif'
duration = 1  # Duration per frame in milliseconds
loop = 0  # loop forever

# Get list of PNG files
images = [img for img in os.listdir(image_folder) if img.endswith('.png')]
images.sort()

# Open images
frames = [Image.open(os.path.join(image_folder, img)) for img in images]

# Save as GIF
frames[0].save(
    output_gif,
    save_all=True,
    append_images=frames[1:],
    duration=duration,
    loop=loop
)

print(f"GIF saved as {output_gif}")
