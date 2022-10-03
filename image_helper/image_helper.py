"""_summary_
"""

import os
from PIL import Image
import numpy as np
from summarizer import Summarizer


class ImageHelper:
    """_summary_
    """

    EXAMPLE_IMAGE_PATH = os.path.join(os.path.dirname(__file__), "example.png")

    @classmethod
    def load_image(cls, path: str, copy_to_output_folder=False) -> Image:
        """_summary_

        Args:
            path (str): _description_
            copy_to_output_folder (bool, optional): _description_. Defaults to False.

        Returns:
            Image: _description_
        """

        img = Image.open(path)

        os.makedirs(Summarizer.SAVE_FOLDER, exist_ok=True)

        if copy_to_output_folder:
            img.save(os.path.join(Summarizer.SAVE_FOLDER, "loaded_image.png"), subsampling=0, quality=100)

        return img

    @classmethod
    def get_default_image(cls) -> Image:
        """_summary_

        Returns:
            Image: _description_
        """

        return cls.load_image(cls.EXAMPLE_IMAGE_PATH, True)

    @classmethod
    def image_to_bytes(cls, image: Image) -> bytes:
        """_summary_

        Args:
            image (Image): _description_

        Returns:
            bytes: _description_
        """

        return bytes(np.array(image).flatten())

    @classmethod
    def save_bytes_as_image(cls, data: bytes, path: str, width: int,
                            height: int, channels: int):
        """_summary_

        Args:
            data (bytes): _description_
            path (str): _description_
            width (int): _description_
            height (int): _description_
            channels (int): _description_
        """

        path = os.path.join(Summarizer.SAVE_FOLDER, path)

        data = data[:width * height * channels]

        data = np.frombuffer(data, dtype=np.uint8).reshape((height, width, channels))

        os.makedirs(os.path.dirname(path), exist_ok=True)

        img = Image.fromarray(data)
        img.putalpha(255)
        
        img.save(path, subsampling=0, quality=100)
