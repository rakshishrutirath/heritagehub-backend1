import base64
import mimetypes
import requests

from django.conf import settings


# ============================================================
# MESHY API
# ============================================================

MESHY_CREATE_URL = (
    "https://api.meshy.ai/openapi/v1/image-to-3d"
)

MESHY_TASK_URL = (
    "https://api.meshy.ai/openapi/v1/image-to-3d/{}"
)


# ============================================================
# FILE SIZE LIMIT
# ============================================================

# Your Django/Cloudinary setup currently allows 10 MB.
MAX_MODEL_SIZE = 10 * 1024 * 1024


# ============================================================
# IMAGE -> DATA URI
# ============================================================

def image_file_to_data_uri(image_field):
    """
    Convert Django uploaded image into a base64 data URI
    that Meshy can accept.
    """

    mime_type, _ = mimetypes.guess_type(
        image_field.name
    )

    if not mime_type:
        mime_type = "image/jpeg"

    image_field.open("rb")

    try:
        image_bytes = image_field.read()
    finally:
        image_field.close()

    encoded = base64.b64encode(
        image_bytes
    ).decode("utf-8")

    return f"data:{mime_type};base64,{encoded}"


# ============================================================
# CREATE MESHY IMAGE-TO-3D TASK
# ============================================================

def create_meshy_task(image_field):

    # --------------------------------------------------------
    # Check API key
    # --------------------------------------------------------

    if not settings.MESHY_API_KEY:

        return {
            "error": True,
            "detail": "Meshy API key is missing."
        }

    # --------------------------------------------------------
    # Convert image to data URI
    # --------------------------------------------------------

    try:
        image_data_uri = image_file_to_data_uri(
            image_field
        )

    except Exception as exc:

        return {
            "error": True,
            "detail": (
                "Could not read uploaded image: "
                f"{str(exc)}"
            )
        }

    # --------------------------------------------------------
    # Headers
    # --------------------------------------------------------

    headers = {
        "Authorization": (
            f"Bearer {settings.MESHY_API_KEY}"
        ),
        "Content-Type": "application/json",
    }

    # --------------------------------------------------------
    # Meshy request
    #
    # IMPORTANT:
    #
    # Smart Topology + meshy-t2 allows us to control
    # the polygon count.
    #
    # Lower polygon count = much smaller GLB.
    # --------------------------------------------------------

    body = {

        "image_url": image_data_uri,

        # Use Smart Topology for a lightweight model
        "model_type": "smart-topology",

        # Current recommended Smart Topology model
        "ai_model": "meshy-t2",

        # Keep model small enough for your 10 MB limit
        #
        # 4,000 is the safest starting point.
        "target_polycount": 4000,

        # We still want textures
        "should_texture": True,

        # 2K is the lowest supported texture resolution
        # and is much smaller than 4K/8K.
        "texture_resolution": "2k",

        # Only generate GLB
        "target_formats": ["glb"],

        # Don't generate unnecessary PBR maps
        "enable_pbr": False,

        # Automatically improve the input image
        "image_enhancement": True,

    }

    # --------------------------------------------------------
    # Send request to Meshy
    # --------------------------------------------------------

    try:

        response = requests.post(
            MESHY_CREATE_URL,
            headers=headers,
            json=body,
            timeout=90,
        )

    except requests.RequestException as exc:

        return {
            "error": True,
            "detail": (
                "Could not connect to Meshy: "
                f"{str(exc)}"
            )
        }

    # --------------------------------------------------------
    # Check HTTP status
    # --------------------------------------------------------

    if response.status_code not in (
        200,
        201,
        202,
    ):

        return {
            "error": True,
            "detail": (
                f"Meshy returned "
                f"{response.status_code}: "
                f"{response.text[:1000]}"
            )
        }

    # --------------------------------------------------------
    # Parse JSON
    # --------------------------------------------------------

    try:

        data = response.json()

    except ValueError:

        return {
            "error": True,
            "detail": (
                "Meshy returned an invalid JSON response."
            )
        }

    # --------------------------------------------------------
    # Get task ID
    # --------------------------------------------------------

    task_id = data.get("result")

    if not task_id:

        return {
            "error": True,
            "detail": (
                "Meshy did not return a task ID."
            )
        }

    # --------------------------------------------------------
    # Success
    # --------------------------------------------------------

    return {
        "error": False,
        "task_id": task_id,
    }


# ============================================================
# CHECK MESHY TASK
# ============================================================

def get_meshy_task(task_id):

    # --------------------------------------------------------
    # Check API key
    # --------------------------------------------------------

    if not settings.MESHY_API_KEY:

        return {
            "error": True,
            "detail": "Meshy API key is missing."
        }

    # --------------------------------------------------------
    # Headers
    # --------------------------------------------------------

    headers = {
        "Authorization": (
            f"Bearer {settings.MESHY_API_KEY}"
        )
    }

    # --------------------------------------------------------
    # Request task status
    # --------------------------------------------------------

    try:

        response = requests.get(
            MESHY_TASK_URL.format(task_id),
            headers=headers,
            timeout=30,
        )

    except requests.RequestException as exc:

        return {
            "error": True,
            "detail": (
                "Could not connect to Meshy: "
                f"{str(exc)}"
            )
        }

    # --------------------------------------------------------
    # Check status
    # --------------------------------------------------------

    if response.status_code != 200:

        return {
            "error": True,
            "detail": (
                f"Meshy returned "
                f"{response.status_code}: "
                f"{response.text[:1000]}"
            )
        }

    # --------------------------------------------------------
    # Parse JSON
    # --------------------------------------------------------

    try:

        data = response.json()

    except ValueError:

        return {
            "error": True,
            "detail": (
                "Meshy returned invalid JSON."
            )
        }

    # --------------------------------------------------------
    # Return task data
    # --------------------------------------------------------

    return {
        "error": False,
        "data": data,
    }


# ============================================================
# DOWNLOAD GLB
# ============================================================

def download_glb(glb_url):
    """
    Download the GLB file from Meshy.

    Returns:
        {
            "error": False,
            "content": bytes,
            "size": int
        }

    or:

        {
            "error": True,
            "detail": str
        }
    """

    if not glb_url:

        return {
            "error": True,
            "detail": "GLB URL is missing."
        }

    try:

        response = requests.get(
            glb_url,
            timeout=180,
            stream=True,
        )

        response.raise_for_status()

    except requests.RequestException as exc:

        return {
            "error": True,
            "detail": (
                "Could not download GLB from Meshy: "
                f"{str(exc)}"
            )
        }

    # --------------------------------------------------------
    # Download in chunks
    # --------------------------------------------------------

    chunks = []
    total_size = 0

    try:

        for chunk in response.iter_content(
            chunk_size=1024 * 1024
        ):

            if not chunk:
                continue

            chunks.append(chunk)

            total_size += len(chunk)

            # ------------------------------------------------
            # Stop if already larger than allowed size.
            # ------------------------------------------------

            if total_size > MAX_MODEL_SIZE:

                return {
                    "error": True,
                    "detail": (
                        "Meshy generated a GLB larger than "
                        "the 10 MB storage limit. "
                        f"Generated size: "
                        f"{total_size / (1024 * 1024):.2f} MB. "
                        "Try generating with a lower "
                        "polygon count."
                    ),
                    "size": total_size,
                }

    finally:

        response.close()

    content = b"".join(chunks)

    # --------------------------------------------------------
    # Final safety check
    # --------------------------------------------------------

    if len(content) > MAX_MODEL_SIZE:

        return {
            "error": True,
            "detail": (
                "Generated GLB is larger than 10 MB. "
                f"Size: "
                f"{len(content) / (1024 * 1024):.2f} MB."
            ),
            "size": len(content),
        }

    # --------------------------------------------------------
    # Success
    # --------------------------------------------------------

    return {
        "error": False,
        "content": content,
        "size": len(content),
    }