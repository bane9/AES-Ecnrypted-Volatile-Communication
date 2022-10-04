"""Image helper unit tests
"""

from PIL import Image
from ..image_helper import ImageHelper

IMAGE_DIM_X = 100
IMAGE_DIM_Y = 100

IMAGE_CHANNELS = 3

IMAGE_COLOR = 255

WHITE_IMAGE = Image.new("RGBA"[:IMAGE_CHANNELS],
                        (IMAGE_DIM_X, IMAGE_DIM_Y), (IMAGE_COLOR, IMAGE_COLOR, IMAGE_COLOR))

SERIALIZED_IMAGE = ImageHelper.image_to_bytes(WHITE_IMAGE)

def test_image_serialization():
    """Test ImageHelper Image serialization
    """

    assert SERIALIZED_IMAGE == IMAGE_COLOR.to_bytes(1, "big") * IMAGE_DIM_X * IMAGE_DIM_Y * IMAGE_CHANNELS

def test_image_deserialization():
    """Test ImageHelper Image deserialization
    """

    # pylint: disable=protected-access
    assert WHITE_IMAGE == ImageHelper._bytes_to_image(SERIALIZED_IMAGE,
                                                      IMAGE_DIM_X,
                                                      IMAGE_DIM_Y,
                                                      IMAGE_CHANNELS)
