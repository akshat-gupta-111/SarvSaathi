"""
Cloudinary utility functions for image uploads.
All images are uploaded to Cloudinary cloud storage.
"""

import cloudinary
import cloudinary.uploader
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def upload_image_to_cloudinary(image_file, folder="sarvsaathi", public_id=None, transformation=None):
    """
    Upload an image to Cloudinary.
    
    Args:
        image_file: The image file to upload (can be file object, path, or URL)
        folder: Cloudinary folder to store the image (default: "sarvsaathi")
        public_id: Optional custom public ID for the image
        transformation: Optional transformation dict (e.g., {"width": 500, "height": 500, "crop": "fill"})
    
    Returns:
        dict: Contains 'url', 'secure_url', 'public_id' on success
        None: If upload fails or Cloudinary is not configured
    """
    if not settings.CLOUDINARY_URL:
        logger.warning("Cloudinary not configured. Cannot upload image.")
        return None
    
    try:
        upload_options = {
            "folder": folder,
            "resource_type": "image",
            "overwrite": True,
        }
        
        if public_id:
            upload_options["public_id"] = public_id
        
        if transformation:
            upload_options["transformation"] = transformation
        
        result = cloudinary.uploader.upload(image_file, **upload_options)
        
        return {
            'url': result.get('url'),
            'secure_url': result.get('secure_url'),
            'public_id': result.get('public_id'),
            'format': result.get('format'),
            'width': result.get('width'),
            'height': result.get('height'),
        }
    except Exception as e:
        logger.error(f"Failed to upload image to Cloudinary: {str(e)}")
        return None


def upload_avatar(image_file, user_id):
    """
    Upload a user avatar to Cloudinary with optimized settings.
    
    Args:
        image_file: The avatar image file
        user_id: The user's ID for organizing uploads
    
    Returns:
        str: The secure URL of the uploaded avatar, or None if failed
    """
    result = upload_image_to_cloudinary(
        image_file,
        folder="sarvsaathi/avatars",
        public_id=f"user_{user_id}_avatar",
        transformation={
            "width": 300,
            "height": 300,
            "crop": "fill",
            "gravity": "face",  # Focus on face for avatars
            "quality": "auto",
            "fetch_format": "auto",
        }
    )
    
    return result.get('secure_url') if result else None


def upload_document(document_file, user_id, doc_type="document"):
    """
    Upload a document (e.g., medical certificate, license) to Cloudinary.
    
    Args:
        document_file: The document file
        user_id: The user's ID
        doc_type: Type of document for organization
    
    Returns:
        str: The secure URL of the uploaded document, or None if failed
    """
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    
    result = upload_image_to_cloudinary(
        document_file,
        folder=f"sarvsaathi/documents/{doc_type}",
        public_id=f"user_{user_id}_{doc_type}_{unique_id}",
    )
    
    return result.get('secure_url') if result else None


def delete_image_from_cloudinary(public_id):
    """
    Delete an image from Cloudinary.
    
    Args:
        public_id: The public ID of the image to delete
    
    Returns:
        bool: True if deleted successfully, False otherwise
    """
    if not settings.CLOUDINARY_URL:
        logger.warning("Cloudinary not configured. Cannot delete image.")
        return False
    
    try:
        result = cloudinary.uploader.destroy(public_id)
        return result.get('result') == 'ok'
    except Exception as e:
        logger.error(f"Failed to delete image from Cloudinary: {str(e)}")
        return False


def get_cloudinary_url(public_id, transformation=None):
    """
    Get a Cloudinary URL for an image with optional transformations.
    
    Args:
        public_id: The public ID of the image
        transformation: Optional transformation dict
    
    Returns:
        str: The URL of the image
    """
    if not settings.CLOUDINARY_URL:
        return None
    
    try:
        import cloudinary.utils
        options = {"secure": True}
        if transformation:
            options.update(transformation)
        
        return cloudinary.utils.cloudinary_url(public_id, **options)[0]
    except Exception as e:
        logger.error(f"Failed to generate Cloudinary URL: {str(e)}")
        return None
