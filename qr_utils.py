import qrcode
from PIL.ImageQt import ImageQt


def generate_qr(data: str):
    qr = qrcode.make(data)
    return ImageQt(qr)