from PIL import Image
import io
from pathlib import Path
import uuid

class ImageTools:
    UPLOAD_DIR = Path("./uploads/images")
    
    @classmethod
    def save_image(cls, file_bytes: bytes, compress: bool = True) -> str:
        """Save and optionally compress image"""
        cls.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        
        img = Image.open(io.BytesIO(file_bytes))
        
        if compress:
            img = img.convert("RGB")
            img.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
        
        filename = f"{uuid.uuid4()}.jpg"
        filepath = cls.UPLOAD_DIR / filename
        img.save(filepath, "JPEG", quality=85, optimize=True)
        
        return str(filepath)
