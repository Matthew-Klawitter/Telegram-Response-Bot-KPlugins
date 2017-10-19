from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

image = Image.open("assets\doge.jpg")
draw = ImageDraw.Draw(image)

font = ImageFont.truetype("comic.ttf", 32)

draw.text((200, 200), "Much Cafe, So Modular", (0, 128, 0), font)
draw.text((400, 400), "Wow", (0, 0, 255), font)
draw.text((800, 800), "Amazing!", (255, 255, 0), font)
image.save("assets\dogetest.jpg")