
# %%
from os import makedirs
from PIL import Image

# Load the example image
# frame_name = "neon_frame"
# frame_name = "cat_crime_graffiti"
# frame_name = "glitch_unstable"
# frame_name = "speedlines"
# frame_name = "glitch_wave"
# frame_name = "darkage_red"
frame_name = "rain_of_gold"
# frame_name = "christmas_lights"

frame_gif = Image.open(f"../assets/frames/{frame_name}.gif")

image = Image.open("../assets/example/1.png")
width, height = image.size

# Create a black background image
if frame_name.lower() in ["speedlines", "rain_of_gold"]:
    OFFSET = 0
else:
    OFFSET = 275

base_layer = Image.new(mode="RGB", size=(width + OFFSET, height + OFFSET))
# Paste the target image on the base layer
base_layer.paste(image, (OFFSET//2, OFFSET//2))

# Break apart the frame gif, paste it ontop of the base image, and reconstruct it in a list
gif_imgs = []
try:
    while 1:
        # Get the next frame, resize it, and add an alpha layer
        frame_gif.seek(frame_gif.tell()+1)
        frame_img = frame_gif.resize((width + OFFSET, height + OFFSET))
        frame_img = frame_img.convert('RGBA')

        # Copy the base layer image
        temp_img = base_layer.copy()
        # Then the frame on top
        temp_img.paste(frame_img, (0, 0), frame_img)

        # Add this frame to the output list
        gif_imgs.append(temp_img.copy())
except EOFError:
    pass # end of sequence

makedirs("output/", exist_ok=True)
gif_imgs[0].save('output/example.gif',
               save_all = True, append_images = gif_imgs[1:],
               optimize = False, duration = 10, loop=0)

# %%
