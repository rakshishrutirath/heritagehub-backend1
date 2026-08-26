import qrcode
from io import BytesIO
from django.core.files import File


def generate_qr_for_record(record):
    base_url = "https://heritagehub-backend1.onrender.com"
    url = f"{base_url}/heritage/{record.id}/"

    qr_img = qrcode.make(url)

    buffer = BytesIO()
    qr_img.save(buffer, format="PNG")
    buffer.seek(0)

    record.qr_code.save(
        f"{record.id}.png",
        File(buffer),
        save=False
    )