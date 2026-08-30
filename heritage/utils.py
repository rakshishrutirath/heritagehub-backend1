import qrcode
from io import BytesIO
from django.core.files import File


def generate_qr_for_record(record):
    """
    Generate a QR code pointing to the public heritage record page.
    """

    base_url = "https://heritagehub-frontend1.vercel.app"

    url = f"{base_url}/heritage/{record.id}/"

    # Generate QR image
    qr_img = qrcode.make(url)

    # Store image in memory
    buffer = BytesIO()

    qr_img.save(
        buffer,
        format="PNG"
    )

    buffer.seek(0)

    # Attach QR image to the model.
    # The actual storage is handled by Django/Cloudinary.
    record.qr_code.save(
        f"{record.id}.png",
        File(buffer),
        save=False
    )

    buffer.close()

    return record.qr_code