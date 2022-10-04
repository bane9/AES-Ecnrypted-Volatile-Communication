"""Module dedicated to image loading/saving and it's serialization
and deserialization.
"""

import os
from PIL import Image
import numpy as np
from summarizer import Summarizer


class ImageHelper:
    """Class dedicated to image loading/saving and it's serialization
    and deserialization.
    """

    EXAMPLE_IMAGE_PATH = os.path.join(os.path.dirname(__file__), "example.jpg")

    @classmethod
    def load_image(cls, path: str, copy_to_output_folder=False) -> Image:
        """Load an image

        Args:
            path (str): Path to the image
            copy_to_output_folder (bool, optional): If set to True
            the loaded image will be copied to the output folder currently in use. Defaults to False.

        Returns:
            Image: PIL Image instance
        """

        img = Image.open(path)

        os.makedirs(Summarizer.SAVE_FOLDER, exist_ok=True)

        if copy_to_output_folder:
            img.save(os.path.join(Summarizer.SAVE_FOLDER, "loaded_image.png"), subsampling=0, quality=100)

        return img

    @classmethod
    def get_default_image(cls) -> Image:
        """Loads the image located in ImageHelper.EXAMPLE_IMAGE_PATH path

        Returns:
            Image: PIL Image instance
        """

        return cls.load_image(cls.EXAMPLE_IMAGE_PATH, True)

    @classmethod
    def image_to_bytes(cls, image: Image) -> bytes:
        """Convert an Image instance to flat bytes array

        Args:
            image (Image): PIL Image instance

        Returns:
            bytes: Serialized image
        """

        return bytes(np.array(image).flatten())

    @classmethod
    def _bytes_to_image(cls, data: bytes, width: int,
                        height: int, channels: int) -> Image:
        """Deserialize an raw image buffer .

        Args:
            data (bytes): Serialized image
            width (int): Width of the serialized image
            height (int): Height of the serialized image
            channels (int): Number of channels the serialized image has

        Returns:
            bytes: deserialized image
        """

        data = data[:width * height * channels]

        data = np.frombuffer(data, dtype=np.uint8).reshape((height, width, channels))
        return Image.fromarray(data)

    @classmethod
    def save_bytes_as_image(cls, data: bytes, path: str, width: int,
                            height: int, channels: int):
        """Save serialized image as a proper image.

        Args:
            data (bytes): Serialized image
            path (str): Path to save it to
            width (int): Width of the serialized image
            height (int): Height of the serialized image
            channels (int): Number of channels the serialized image has
        """

        path = os.path.join(Summarizer.SAVE_FOLDER, path)

        os.makedirs(os.path.dirname(path), exist_ok=True)

        img = cls._bytes_to_image(data, width, height, channels)
        img.putalpha(255)

        img.save(path, subsampling=0, quality=100)
