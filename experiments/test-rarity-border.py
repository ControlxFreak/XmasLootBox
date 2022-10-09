
# %%
from PIL import Image

# Load the example images
# frame_gif = Image.open("../frames/neon_frame.gif")
# frame_gif = Image.open("../frames/cat_crime_graffiti.gif")
frame_gif = Image.open("../frames/glitch_unstable.gif")
image = Image.open("imgs/cat_santa.png")
width, height = image.size

# Create a black background image
offset = 275
base_layer = Image.new(mode="RGB", size=(width + offset, height + offset))
# Paste the target image on the base layer
base_layer.paste(image, (offset//2, offset//2))

# Break apart the frame gif, paste it ontop of the base image, and reconstruct it in a list
gif_imgs = []
try:
    while 1:
        # Get the next frame, resize it, and add an alpha layer
        frame_gif.seek(frame_gif.tell()+1)
        frame_img = frame_gif.resize((width + offset, height + offset))
        frame_img = frame_img.convert('RGBA')

        # Copy the base layer image
        temp_img = base_layer.copy()
        # Then the frame on top
        temp_img.paste(frame_img, (0, 0), frame_img)

        # Add this frame to the output list
        gif_imgs.append(temp_img.copy())

except EOFError:
    pass # end of sequence

gif_imgs[0].save('imgs/cat_santa_example.gif',
               save_all = True, append_images = gif_imgs[1:],
               optimize = False, duration = 10, loop=0)

# %%
