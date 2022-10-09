# %%
# from PIL import Image, ImageOps
# ImageOps.expand(
#     Image.open('1.png'),
#     border=10,
#     fill='green').save('1-border.png')


# %%
from PIL import Image
from copy import deepcopy
im = Image.open("catframe.gif")

im2 = Image.open("1.png")
width, height = im2.size

ims = []

try:
    while 1:
        im.seek(im.tell()+1)
        im3 = im.resize((width, height))
        im3 = im3.convert('RGBA')

        newImage = []
        for item in im3.getdata():
            if all([v < 25 for v in item[:3]]):
                newImage.append((0, 0, 0, 0))
            else:
                newImage.append(item)

        im3.putdata(newImage)
        imk = im2.copy()
        # imk = imk.resize(width + 250, height + 250)

        imk.paste(im3, (0, 0), im3)
        ims.append(imk.copy())
        # imk.show()

except EOFError:
    pass # end of sequence

ims[0].save('example.gif',
               save_all = True, append_images = ims[1:],
               optimize = False, duration = 10, loop=0)

# %%
