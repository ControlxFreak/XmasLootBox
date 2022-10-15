import os
from PIL import Image
from PIL.Image import Image as ImgType
from typing import List

def add_frame(image: Image, frame_path: str) -> List[ImgType]:
    """Adds an animated GIF frame to an image."""
    # Load the frame
    frame_gif = Image.open(frame_path)

    # Get the image's size
    width, height = 512, 512
    image = image.resize((width, height))

    if os.path.basename(frame_path).lower() in ["speedlines.gif", "rain_of_gold.gif"]:
        # NOTE: The speedlines and rain of gold frames look a lot better
        #       if you don't create a buffer border.
        offset = 0
    else:
        # NOTE: This offset creates a buffer border to prevent the frame from
        #       overlapping the image.
        offset = 140

    # Create the base background image and paste the desired image ontop
    base_layer = Image.new(mode="RGB", size=(width + offset, height + offset))
    base_layer.paste(image, (offset//2, offset//2))

    # Break apart the frame gif, paste it ontop of the base image, and reconstruct it in a list
    output_images = []
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
            output_images.append(temp_img.copy())
    except EOFError:
        pass # end of sequence

    # Return the output gif images
    return output_images
