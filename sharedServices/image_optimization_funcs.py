"""this is the script to optimize images for MFG EV app"""
import io
import base64
from PIL import Image

from django.core.files.base import ContentFile

# pylint:disable=import-error
from sharedServices.constants import (
    FULL_QUALITY_COMPRESSION,
    IMAGE_SIZES_AND_QUALITY,
    RGB_CONVERSION_MODE,
    JPEG_FORMAT,
)

# this constant is initialized to provide different
# conversion types for different types of images


def convert_image_to_jpeg(image_obj):
    """this function converts images in jpeg format which are not in
    jpeg format"""
    return image_obj.convert(RGB_CONVERSION_MODE)


def optimize_image(
    image,
    image_name,
    image_type,
    image_str=None,
    only_resize=False,
    image_format="JPEG"
):
    """this functions contains logic to get unoptimized image and
    optimize it by maintaining original quality while exactly matching size requirements."""
    if image.format == "GIF" and image_str:
        return ContentFile(
            base64.b64decode(image_str),
            name=image_name
        )
    size, _ = IMAGE_SIZES_AND_QUALITY.get(image_type)
    
    # if image extesion is not jpeg then image will be converted to jpeg
    if only_resize is False:
        if image.format != JPEG_FORMAT:
            image = convert_image_to_jpeg(image)
        
        if size:
            # Directly resize to target size without maintaining aspect ratio
            resized_image = image.resize(size, Image.Resampling.LANCZOS)
            # Save with maximum quality
            output_buffer = io.BytesIO()
            resized_image.save(output_buffer, image_format, quality=100)
            return ContentFile(output_buffer.getvalue(), image_name)
        else:
            # If no size requirement, just save with high quality
            output_buffer = io.BytesIO()
            image.save(output_buffer, image_format, quality=100)
            return ContentFile(output_buffer.getvalue(), image_name)
    else:
        # Only resize mode
        if size:
            # Directly resize to target size without maintaining aspect ratio
            resized_image = image.resize(size, Image.Resampling.LANCZOS)
        else:
            resized_image = image
            
        # Save with maximum quality
        output_buffer = io.BytesIO()
        resized_image.save(output_buffer, image_format, quality=100)
        return ContentFile(output_buffer.getvalue(), image_name)
