# Imager

A lightweight Python utility for resizing and composing images using Pillow.  
Supports blurred backgrounds, borders, and intelligent aspect-ratio fitting.

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
imager = Imager(output_size=(700, 365), config=Config())
output = imager.process_image(input_image)

if output:
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

## Requirements

    Python ≥ 3.13
    Pillow ≥ 10.0

## To Do:

- [ ] Add input and output images to illustrate functionality

## License

MIT © 2025 