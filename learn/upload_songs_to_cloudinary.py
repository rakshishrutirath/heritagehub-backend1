import os
import django
from pathlib import Path

# --------------------------------------------------
# Django setup
# --------------------------------------------------

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heritagehub.settings")
django.setup()

# --------------------------------------------------
# Imports
# --------------------------------------------------

from django.conf import settings
from learn.models import Song
import cloudinary.uploader


# --------------------------------------------------
# Upload function
# --------------------------------------------------

def upload_songs():
    print("=" * 70)
    print("CLOUDINARY SONG UPLOAD")
    print("=" * 70)

    success = 0
    skipped = 0
    failed = 0

    songs = Song.objects.filter(audio__isnull=False).exclude(audio="")

    print(f"Songs found: {songs.count()}")
    print()

    for song in songs:

        print("-" * 70)
        print(f"ID: {song.id}")
        print(f"Title: {song.title}")
        print(f"Database file: {song.audio.name}")

        # --------------------------------------------------
        # Skip if already uploaded
        # --------------------------------------------------

        if song.cloudinary_audio_url:
            print("SKIPPED - Cloudinary URL already exists")
            skipped += 1
            continue

        # --------------------------------------------------
        # Local file path
        # --------------------------------------------------

        file_path = Path(settings.MEDIA_ROOT) / song.audio.name

        print(f"Local file: {file_path}")

        if not file_path.exists():
            print("FAILED - Local file does not exist")
            failed += 1
            continue

        # --------------------------------------------------
        # Cloudinary public ID
        # --------------------------------------------------

        file_name = Path(song.audio.name).stem

        # Remove characters that can cause problems
        safe_name = "".join(
            c if c.isalnum() or c in "_-" else "_"
            for c in file_name
        )

        public_id = f"learn_songs/{safe_name}"

        print(f"Cloudinary public ID: {public_id}")

        try:

            # --------------------------------------------------
            # Upload as RAW
            # --------------------------------------------------

            result = cloudinary.uploader.upload(
                str(file_path),
                resource_type="raw",
                public_id=public_id,
                overwrite=True
            )

            cloudinary_url = result["secure_url"]

            # --------------------------------------------------
            # Save URL in database
            # --------------------------------------------------

            song.cloudinary_audio_url = cloudinary_url
            song.save(update_fields=["cloudinary_audio_url"])

            print("SUCCESS")
            print(f"URL: {cloudinary_url}")

            success += 1

        except Exception as e:

            print("FAILED")
            print(f"Error: {e}")

            failed += 1

    # --------------------------------------------------
    # Final summary
    # --------------------------------------------------

    print()
    print("=" * 70)
    print("UPLOAD COMPLETE")
    print("=" * 70)

    print(f"Successful : {success}")
    print(f"Skipped    : {skipped}")
    print(f"Failed     : {failed}")

    print("=" * 70)


# --------------------------------------------------
# Run
# --------------------------------------------------

if __name__ == "__main__":
    upload_songs()