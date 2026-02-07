import qrcode
from PIL.ImageQt import ImageQt

def generate_qr(data: str):
    qr = qrcode.make(data)
    pil_img = qr.get_image() if hasattr(qr, "get_image") else qr
    return ImageQt(pil_img.convert("RGB"))