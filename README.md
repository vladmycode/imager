# Imager

A lightweight Python library for resizing and composing images.  
It supports blurred backgrounds, borders, and intelligent aspect-ratio fitting.

## Installation

```bash
uv add git+https://github.com/vladmycode/imager.git
```

or

```bash
pip install git+https://github.com/vladmycode/imager.git
```

## Usage

```python
from PIL import Image
from imager import Imager, Config

input_image = Image.open("example.jpg")

# Generate a 700x365 px image from the source `example.jpg`
imager = Imager(output_size=(700, 365), config=Config())
output = imager.process_image(input_image)

if output is not None:
    output.save("output.jpg")
```

## Config Options
| Name                    | Type            | Default                                  | Description                       |
| ----------------------- | --------------- | ---------------------------------------- | --------------------------------- |
| background_blur         | bool            | True                                     | Apply Gaussian blur to background |
| background_blur_radius  | int             | 75                                       | Blur intensity                    |
| foreground_border       | bool            | True                                     | Add border to foreground          |
| foreground_border_width | int             | 1                                        | Border thickness                  |
| foreground_border_color | tuple[int, ...] | (255, 255, 255)                          | Border color                      |
| force_fit	bool          | True            | Crop to fill template instead of padding |

## Examples

### Example 1: Generate a 1920x1080 px image from a 200x150 px image

```python
from PIL import Image
from imager import Config, Imager

input_image = Image.open("examples/200x150_toosmall.png")
config = Config(
    foreground_border_width=15,
    foreground_border_color=(255, 255, 255, 35), # 35 transparency
    force_fit=False,
)
imager = Imager(output_size=(1920, 1080), config=config)
output = imager.process_image(input_image)
```

![Combo 1](examples/200x150_toosmall.jpg)
*A 200×150 px image is transformed into a 1920×1080 px composition. The original (foreground) image is enlarged to 400×300 px, given a 15 px semi-transparent border, and then placed over a blurred 1920×1080 px background generated from the same source image.*


### Example 2: Generate a 1920x1080 px image from a 300x600 px image (portrait)

```python
from PIL import Image
from imager import Config, Imager

input_image = Image.open("examples/300x600_portrait.png")
config = Config(
    foreground_border_width=15,
    foreground_border_color=(255, 255, 255, 35), # 35 transparency
    force_fit=False,
)
imager = Imager(output_size=(1920, 1080), config=config)
output = imager.process_image(input_image)
```

![Combo 2](examples/300x600_portrait.jpg)
*A 300x600 px image is transformed into a 1920×1080 px composition. The original (foreground) image is resized, given a 15 px semi-transparent border, and then placed over a blurred 1920×1080 px background generated from the same source image.*

### Example 3: Generate a 1920x1080 px image from a 1200x400 px image (extrawide)

```python
from PIL import Image
from imager import Config, Imager

input_image = Image.open("examples/1200x400_extrawidelandscape.png")
config = Config(
    foreground_border_width=15,
    foreground_border_color=(255, 255, 255, 35), # 35 transparency
    force_fit=False,
)
imager = Imager(output_size=(1920, 1080), config=config)
output = imager.process_image(input_image)
```

![Combo 3](examples/1200x400_extrawidelandscape.jpg)
*A 1200x400 px image is transformed into a 1920×1080 px composition. The original (foreground) image is resized, given a 15 px semi-transparent border, and then placed over a blurred 1920×1080 px background generated from the same source image.*

## Requirements

    Python ≥ 3.13
    Pillow ≥ 10.0

## License

MIT © 2025 