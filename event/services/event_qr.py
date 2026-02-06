import qrcode
from io import BytesIO
from django.core.files.base import ContentFile


def generate_qr_code(data: str, filename: str = "qr.png"):
    """
    Generate a QR code image from given data and return as Django ContentFile.

    :param data: String data to encode in the QR code
    :param filename: Optional filename for the QR image
    :return: (filename, ContentFile)
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return filename, ContentFile(buffer.getvalue())

