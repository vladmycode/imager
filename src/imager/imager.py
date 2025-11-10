import logging
from dataclasses import dataclass

from PIL import Image, ImageFilter, ImageOps

logger = logging.getLogger(__name__)


@dataclass
class Config:
    """
    Settings for image composition.

    Attributes:
        background_blur (bool): Apply Gaussian blur to backgrounds (default: True).
        background_blur_radius (int): Blur strength (default: 75).
        foreground_border (bool): Add a border to the foreground (default: True).
        foreground_border_width (int): Border thickness in pixels (default: 1).
        foreground_border_color (tuple[int, ...]): Border color RGB/RGBA, 0–255
        (default: (255, 255, 255)).
        force_fit (bool): If True, crop to fill template; if False, keep proportions
        with blurred background (default: True).
    """

    background_blur: bool = True
    background_blur_radius: int = 75
    foreground_border: bool = True
    foreground_border_width: int = 1
    foreground_border_color: tuple[int, ...] = (255, 255, 255)
    force_fit: bool = True


class Imager:
    """
    Class used to manipulate images.
    """

    # Cap upscaling at 2x original size to avoid pixelation.
    SCALE_UP_LIMIT = 2.0

    def __init__(
        self,
        output_size: tuple[int, int] = (700, 365),
        config: Config | None = None,
    ) -> None:
        self.output_width = output_size[0]
        self.output_height = output_size[1]
        self.config = config or Config()

    def process_image(self, image: Image.Image) -> Image.Image | None:
        """
        Creates a new PIL image from `image` by resizing it
        to fit the template dimensions.

        Args:
            image (Image.Image): A PIL image object
        """
        if not isinstance(image, Image.Image):
            raise ValueError("Source image must be a PIL Image object")
        return self._resize_to_template(image)

    def is_template_landscape(self) -> bool:
        """
        Check if the template is landscape oriented.
        """
        return self.output_width > self.output_height

    def is_template_portrait(self) -> bool:
        """
        Check if the template is portrait/vertical oriented.
        """
        return self.output_width < self.output_height

    def _resize_to_template(self, image: Image.Image) -> Image.Image | None:
        """
        Resize the given `image` to fit the template (landscape or portrait).

        Args:
            image (Image.Image): The image to resize.
        """
        try:
            image = self._convert_image_mode(image)
            if self.is_image_too_small_for_template(image):
                return self._create_combo(image)
            if self.is_template_landscape():
                return self._handle_landscape_template(image)
            return self._handle_portrait_template(image)

        except (OSError, ValueError, Image.UnidentifiedImageError) as err:
            logger.error("Unable to resize image: %s", err)
            return None

    def _handle_landscape_template(self, image: Image.Image) -> Image.Image | None:
        """
        Resizes the `image` to fit a landscape template.

        Args:
            image (Image.Image): The image to be processed.
        """
        if self.is_image_portrait(image) or self.is_image_too_narrow_for_template(
            image
        ):
            return (
                self._fit_portrait_to_landscape(image)
                if self.config.force_fit
                else self._create_combo(image)
            )
        return self._fit_wide_to_landscape(image)

    def _handle_portrait_template(self, image: Image.Image) -> Image.Image | None:
        """
        Resizes the `image` to fit a portrait template.

        Args:
            image (Image.Image): The image to be processed.
        """
        if self.is_image_landscape(image) or self.is_image_too_wide_for_template(image):
            return (
                self._fit_landscape_to_portrait(image)
                if self.config.force_fit
                else self._create_combo(image)
            )
        return self._fit_tall_to_portrait(image)

    def _convert_image_mode(self, image: Image.Image) -> Image.Image:
        """
        Returns the `image` converted to RGBA or RGB mode,
        or the original, nonconverted input image, if it has a different mode.

        Args:
            image (Image.Image): The image to be processed
        """
        if image.mode == "P":
            image = image.convert("RGBA")
        if image.mode == "RGBA":
            image = image.convert("RGB")
        return image

    def _fit_portrait_to_landscape(self, image: Image.Image) -> Image.Image:
        """
        Resizes and crops a portrait `image` to fit a landscape template.

        Args:
            image (Image.Image): The original image to be resized and cropped.
        """
        projected_w = self.output_width
        projected_h = int(self.output_width * image.height / image.width)

        resized = image.resize(
            (projected_w, projected_h), resample=Image.Resampling.LANCZOS
        )
        crop_box = (
            0,
            (projected_h - self.output_height) // 4,
            self.output_width,
            (projected_h - self.output_height) // 4 + self.output_height,
        )
        return resized.crop(crop_box)

    def _fit_landscape_to_portrait(self, image: Image.Image) -> Image.Image:
        """
        Resizes and crops a landscape `image` to fit a portrait template.

        Args:
            image (Image.Image): The original image to be resized and cropped.
        """
        projected_h = self.output_height
        projected_w = int(self.output_height * image.width / image.height)

        resized = image.resize(
            (projected_w, projected_h), resample=Image.Resampling.LANCZOS
        )
        crop_box = (
            (projected_w - self.output_width) // 4,
            0,
            (projected_w - self.output_width) // 4 + self.output_width,
            self.output_height,
        )
        return resized.crop(crop_box)

    def _fit_wide_to_landscape(self, image: Image.Image) -> Image.Image:
        """
        Fits a wide `image` to a landscape template, either by resizing and
        cropping or by proportional resizing.

        Args:
            image (Image.Image): The image to be processed.
        """
        if self.config.force_fit:
            projected_w = int(self.output_height * image.width / image.height)
            resized = image.resize(
                (projected_w, self.output_height), resample=Image.Resampling.LANCZOS
            )
            crop_box = (
                (projected_w - self.output_width) // 2,
                0,
                (projected_w - self.output_width) // 2 + self.output_width,
                self.output_height,
            )
            return resized.crop(crop_box)
        return self._resize_proportionally(image)

    def _fit_tall_to_portrait(self, image: Image.Image) -> Image.Image:
        """
        Fits a tall `image` to a portrait template, either by resizing and
        cropping or by proportional resizing.

        Args:
            image (Image.Image): The image to be processed.
        """
        if self.config.force_fit:
            projected_h = int(self.output_width * image.height / image.width)
            resized = image.resize(
                (self.output_width, projected_h), resample=Image.Resampling.LANCZOS
            )
            crop_box = (
                0,
                (projected_h - self.output_height) // 2,
                self.output_width,
                (projected_h - self.output_height) // 2 + self.output_height,
            )
            return resized.crop(crop_box)
        return self._resize_proportionally(image)

    def _resize_proportionally(self, image: Image.Image) -> Image.Image:
        """
        Resizes the `image` proportionally to fit the template dimensions.

        Args:
            image (Image.Image): The image to be resized.
        """
        if self.is_template_landscape():
            projected_h = int(self.output_width * image.height / image.width)
            return image.resize(
                (self.output_width, projected_h), resample=Image.Resampling.LANCZOS
            )
        projected_w = int(self.output_height * image.width / image.height)
        return image.resize(
            (projected_w, self.output_height), resample=Image.Resampling.LANCZOS
        )

    def _create_combo(self, image: Image.Image) -> Image.Image | None:
        """
        Composes a new image from the the given `image`, resized
        proportionally and used as a bordered foreground placed
        centered on a blurred background.

        Args:
            image (Image.Image): The image to be processed.
        """
        try:
            foreground = self._create_foreground_image(image)
            background = self._create_background_image(image)

            top_left_x = (self.output_width - foreground.width) // 2
            top_left_y = (self.output_height - foreground.height) // 2

            # Use the alpha channel for pasting if foreground is RGBA
            if foreground.mode == "RGBA":
                background.paste(foreground, (top_left_x, top_left_y), foreground)
            else:
                background.paste(foreground, (top_left_x, top_left_y))
            return background
        except (OSError, ValueError, Image.UnidentifiedImageError) as err:
            logger.error("Unable to create combo image: %s", err)
            return None

    def _create_foreground_image(self, image: Image.Image) -> Image.Image:
        """
        Returns the `image` prepared to be used as foreground by resizing
        it and adding a colored border.

        Args:
            image (Image.Image): The image to be used for creating the foreground.
        """
        foreground = image.copy()
        foreground = self._resize_foreground(foreground)
        foreground = ImageOps.autocontrast(foreground)
        foreground = self._apply_border(foreground)
        return foreground

    def _resize_foreground(self, image: Image.Image) -> Image.Image:
        """
        Resizes the `image` to fit 80% of the template while maintaining aspect ratio.

        Args:
            image (Image.Image): The image to be processed.
        """
        max_w = int(self.output_width * 0.8)
        max_h = int(self.output_height * 0.8)

        if self._should_scale_up(image, max_w, max_h):
            return self._scale_up_image(image, max_w, max_h)

        # Scale down using thumbnail (maintains aspect ratio, never enlarges)
        image.thumbnail((max_w, max_h), resample=Image.Resampling.LANCZOS)
        return image

    def _should_scale_up(self, image: Image.Image, max_w: int, max_h: int) -> bool:
        """
        Check if `image` is smaller than the bounding box.

        Args:
            image (Image.Image): The image to be processed.
            max_w (int): Maximum allowed width.
            max_h (int): Maximul allowed height.
        """
        return image.width < max_w and image.height < max_h

    def _scale_up_image(
        self, image: Image.Image, max_w: int, max_h: int
    ) -> Image.Image:
        """
        Scales up a small `image`, capped at SCALE_UP_LIMIT.

        Args:
            image (Image.Image): The image to be processed.
            max_w (int): Maximum allowed width.
            max_h (int): Maximum allowed height.
        """
        orig_w, orig_h = image.size

        ratio_w = max_w / orig_w
        ratio_h = max_h / orig_h
        fit_ratio = min(ratio_w, ratio_h)
        scale_ratio = min(fit_ratio, self.SCALE_UP_LIMIT)

        new_w = int(orig_w * scale_ratio)
        new_h = int(orig_h * scale_ratio)

        if new_w > 0 and new_h > 0:
            return image.resize((new_w, new_h), resample=Image.Resampling.LANCZOS)
        return image

    def _apply_border(self, image: Image.Image) -> Image.Image:
        """
        Applies a border to the foreground `image`, if configured.

        Args:
            image (Image.Image): The image to be processed.
        """
        if (
            not self.config.foreground_border
            or self.config.foreground_border_width <= 0
        ):
            return image

        has_transparent_border = len(self.config.foreground_border_color) == 4
        image = self._convert_image_for_border(image, has_transparent_border)

        border_width = self._calculate_safe_border_width(image)
        if border_width > 0:
            image = ImageOps.expand(
                image,
                border=border_width,
                fill=self.config.foreground_border_color,
            )

        return image

    def _convert_image_for_border(
        self, image: Image.Image, has_transparent_border: bool
    ) -> Image.Image:
        """
        Converts the `image` to appropriate mode for border application.

        Args:
            image (Image.Image): The image to be processed.
            has_transparent_border (bool): Border transparency setting.
        """
        if has_transparent_border:
            if image.mode != "RGBA":
                return image.convert("RGBA")
        else:
            if image.mode == "RGBA":
                return image.convert("RGB")
        return image

    def _calculate_safe_border_width(self, image: Image.Image) -> int:
        """
        Calculates the `image` border width that fits within template bounds.

        Args:
            image (Image.Image): The image to be bordered.
        """
        max_allowed_border = min(
            (self.output_width - image.width) // 2,
            (self.output_height - image.height) // 2,
        )

        border_width = self.config.foreground_border_width

        if 0 < max_allowed_border < border_width:
            logger.warning(
                "Foreground border width (%d) reduced to %d to fit within template bounds.",
                border_width,
                max_allowed_border,
            )
            border_width = max_allowed_border

        return border_width

    def _create_background_image(self, image: Image.Image) -> Image.Image:
        """
        Returns a PIL 'image' resized to the template's dimensions to
        be used as background.

        Args:
            image (Image.Image): The image to be used for creating
            the background.
        """
        image_copy = image.copy()
        canvas = self._resize_image_for_background(image_copy)
        crop_box = self._calculate_background_crop_box(canvas)
        background = self._crop_image_and_ensure_size(canvas, crop_box)

        if self.config.background_blur:
            background = background.filter(
                ImageFilter.GaussianBlur(radius=self.config.background_blur_radius)
            )

        return background

    def _resize_image_for_background(self, image: Image.Image) -> Image.Image:
        """
        Resizes the `image` for background, covering the entire template.

        Args:
            image (Image.Image): The image to be processed.
        """
        canvas_w, canvas_h = self._calculate_canvas_dimensions(image)

        if canvas_w <= 0 or canvas_h <= 0:
            logger.warning("Invalid canvas size calculated for background.")
            return Image.new("RGB", (self.output_width, self.output_height))

        return image.resize((canvas_w, canvas_h), resample=Image.Resampling.LANCZOS)

    def _calculate_canvas_dimensions(self, image: Image.Image) -> tuple[int, int]:
        """
        Calculates canvas dimensions based on template orientation
        and image aspect ratio.

        Args:
            image (Image.Image): The image to be processed.
        """
        if self.is_template_landscape():
            return self._calculate_landscape_canvas(image)
        return self._calculate_portrait_canvas(image)

    def _calculate_landscape_canvas(self, image: Image.Image) -> tuple[int, int]:
        """
        Calculate canvas dimensions for landscape template.

        Args:
            image (Image.Image): The image to be processed.
        """
        image_ratio = image.width / image.height
        template_ratio = self.output_width / self.output_height

        if image_ratio < template_ratio:
            # Image is narrower, fit by width
            canvas_w = self.output_width
            canvas_h = int(self.output_width * image.height / image.width)
        else:
            # Image is wider, fit by height
            canvas_h = self.output_height
            canvas_w = int(self.output_height * image.width / image.height)

        return canvas_w, canvas_h

    def _calculate_portrait_canvas(self, image: Image.Image) -> tuple[int, int]:
        """
        Calculate canvas dimensions for portrait template.

        Args:
            image (Image.Image): The image to be processed.
        """
        image_ratio = image.width / image.height
        template_ratio = self.output_width / self.output_height

        if image_ratio > template_ratio:
            # Image is wider, fit by height
            canvas_h = self.output_height
            canvas_w = int(self.output_height * image.width / image.height)
        else:
            # Image is narrower, fit by width
            canvas_w = self.output_width
            canvas_h = int(self.output_width * image.height / image.width)

        return canvas_w, canvas_h

    def _calculate_background_crop_box(
        self, canvas: Image.Image
    ) -> tuple[int, int, int, int]:
        """
        Calculates the crop box to center the canvas on the template.

        Args:
            canvas (Image.Image): The image to be used as canvas.
        """
        canvas_w, canvas_h = canvas.size

        left = max(0, (canvas_w - self.output_width) // 2)
        top = max(0, (canvas_h - self.output_height) // 2)
        right = min(canvas_w, left + self.output_width)
        bottom = min(canvas_h, top + self.output_height)

        return (left, top, right, bottom)

    def _crop_image_and_ensure_size(
        self, canvas: Image.Image, crop_box: tuple[int, int, int, int]
    ) -> Image.Image:
        """
        Crops the canvas and ensures final size matches template exactly.

        Args:
            canvas (Image.Image): The image to be resized.
            crop_box (tuple[int, int, int, int]): Crop coordinates.
        """
        background = canvas.crop(crop_box)

        # Handle potential rounding errors
        if background.size != (self.output_width, self.output_height):
            background = background.resize(
                (self.output_width, self.output_height),
                resample=Image.Resampling.LANCZOS,
            )

        return background

    def is_image_portrait(self, image: Image.Image) -> bool:
        """
        Checks if `image` has a portrait aspect ratio.

        Args:
            image (Image.Image): The image to be bordered.
        """
        return image.width < image.height

    def is_image_landscape(self, image: Image.Image) -> bool:
        """
        Checks if `image` has a landscape aspect ratio.

        Args:
            image (Image.Image): The image to be bordered.
        """
        return image.width > image.height

    def is_image_square(self, image: Image.Image) -> bool:
        """
        Checks if `image` width is equal to its height.

        Args:
            image (Image.Image): The image to be bordered.
        """
        return not self.is_image_portrait(image) and not self.is_image_landscape(image)

    def is_image_too_small_for_template(self, image: Image.Image) -> bool:
        """
        Checks if the width or the height of the `image` is smaller
        than that of the template.

        Args:
            image (Image.Image): The image to be bordered.
        """
        threshold = 0.75
        return (
            image.width < threshold * self.output_width
            or image.height < threshold * self.output_height
        )

    def is_image_too_narrow_for_template(self, image: Image.Image) -> bool:
        """
        Checks if the aspect ratio of the `image`
        is smaller than the aspect ratio of the template.

        Args:
            image (Image.Image): The image to be bordered.
        """
        return image.width / image.height < self.output_width / self.output_height

    def is_image_too_wide_for_template(self, image: Image.Image) -> bool:
        """
        Checks if the aspect ratio of the `image` is greater than
        the aspect ratio of the template.

        Args:
            image (Image.Image): The image to be bordered.
        """
        return image.width / image.height > self.output_width / self.output_height
