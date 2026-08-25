import base64
import mimetypes
import requests

from django.conf import settings


MESHY_CREATE_URL = "https://api.meshy.ai/openapi/v1/image-to-3d"
MESHY_TASK_URL = "https://api.meshy.ai/openapi/v1/image-to-3d/{}"


def image_file_to_data_uri(image_field):
    mime_type, _ = mimetypes.guess_type(image_field.name)

    if not mime_type:
        mime_type = "image/jpeg"

    image_field.open("rb")
    encoded = base64.b64encode(image_field.read()).decode("utf-8")
    image_field.close()

    return f"data:{mime_type};base64,{encoded}"


def create_meshy_task(image_field):
    if not settings.MESHY_API_KEY:
        return {
            "error": True,
            "detail": "Meshy API key is missing."
        }

    image_data_uri = image_file_to_data_uri(image_field)

    headers = {
        "Authorization": f"Bearer {settings.MESHY_API_KEY}",
        "Content-Type": "application/json",
    }

    body = {
        "image_url": image_data_uri,
        "should_texture": True,
        "target_formats": ["glb"],
    }

    try:
        response = requests.post(
            MESHY_CREATE_URL,
            headers=headers,
            json=body,
            timeout=60,
        )
    except requests.RequestException as exc:
        return {
            "error": True,
            "detail": f"Could not connect to Meshy: {str(exc)}"
        }

    if response.status_code not in (200, 201, 202):
        return {
            "error": True,
            "detail": f"Meshy returned {response.status_code}: {response.text[:500]}"
        }

    data = response.json()

    task_id = data.get("result")

    if not task_id:
        return {
            "error": True,
            "detail": "Meshy did not return a task ID."
        }

    return {
        "error": False,
        "task_id": task_id,
    }


def get_meshy_task(task_id):
    if not settings.MESHY_API_KEY:
        return {
            "error": True,
            "detail": "Meshy API key is missing."
        }

    headers = {
        "Authorization": f"Bearer {settings.MESHY_API_KEY}"
    }

    try:
        response = requests.get(
            MESHY_TASK_URL.format(task_id),
            headers=headers,
            timeout=30,
        )
    except requests.RequestException as exc:
        return {
            "error": True,
            "detail": f"Could not connect to Meshy: {str(exc)}"
        }

    if response.status_code != 200:
        return {
            "error": True,
            "detail": f"Meshy returned {response.status_code}: {response.text[:500]}"
        }

    data = response.json()

    return {
        "error": False,
        "data": data,
    }