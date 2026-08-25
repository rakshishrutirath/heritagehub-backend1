import qrcode
from io import BytesIO
from django.core.files import File

def generate_qr_for_record(record):
    # Update this to your real deployed domain once Part 14 is done
    base_url = "https://heritagehub-backend.onrender.com"
    url = f"{base_url}/heritage/{record.id}/"
    qr_img = qrcode.make(url)
    buffer = BytesIO()
    qr_img.save(buffer, format='PNG')
    record.qr_code.save(f"{record.id}.png", File(buffer), save=False)