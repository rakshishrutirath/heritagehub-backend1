import requests

from django.core.files.base import ContentFile

from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from .models import ThreeDGeneration
from .services import (
    create_meshy_task,
    get_meshy_task,
)


# ============================================================
# DOWNLOAD MESHY GLB AND SAVE LOCALLY
# ============================================================

def save_meshy_model_locally(generation, glb_url):
    """
    Download the GLB file from Meshy and save it
    into the Django model_file field.

    This prevents the frontend from directly accessing
    assets.meshy.ai and avoids the browser CORS problem.
    """

    if not glb_url:
        return {
            "success": False,
            "error": "No GLB URL was provided by Meshy."
        }

    try:
        response = requests.get(
            glb_url,
            timeout=120
        )

        response.raise_for_status()

        content = response.content

        if not content:
            return {
                "success": False,
                "error": "Meshy returned an empty GLB file."
            }

        # Save GLB into model_file
        generation.model_file.save(
            f"{generation.id}.glb",
            ContentFile(content),
            save=False
        )

        # Keep the original Meshy URL in the database
        generation.model_url = glb_url

        generation.status = "succeeded"
        generation.error_message = None

        generation.save(
            update_fields=[
                "model_file",
                "model_url",
                "status",
                "error_message",
            ]
        )

        return {
            "success": True
        }

    except requests.RequestException as exc:
        return {
            "success": False,
            "error": (
                "Could not download GLB from Meshy: "
                f"{str(exc)}"
            )
        }

    except Exception as exc:
        return {
            "success": False,
            "error": (
                "Could not save generated GLB: "
                f"{str(exc)}"
            )
        }


# ============================================================
# GENERATE 3D MODEL FROM IMAGE
# ============================================================

@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def generate_3d_from_image(request):

    image = request.FILES.get("image")

    if not image:
        return Response(
            {
                "status": "error",
                "detail": "Please upload an image.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # --------------------------------------------------------
    # Create database record
    # --------------------------------------------------------

    try:
        generation = ThreeDGeneration.objects.create(
            image=image,
            status="pending",
        )

    except Exception as e:
        return Response(
            {
                "status": "error",
                "detail": (
                    "Could not create generation record: "
                    f"{str(e)}"
                ),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # --------------------------------------------------------
    # Send image to Meshy
    # --------------------------------------------------------

    try:
        result = create_meshy_task(
            generation.image
        )

    except Exception as e:

        generation.status = "failed"
        generation.error_message = str(e)

        generation.save(
            update_fields=[
                "status",
                "error_message",
            ]
        )

        return Response(
            {
                "status": "error",
                "generation_id": generation.id,
                "detail": str(e),
            },
            status=status.HTTP_502_BAD_GATEWAY,
        )

    # --------------------------------------------------------
    # Meshy request failed
    # --------------------------------------------------------

    if result.get("error"):

        generation.status = "failed"

        generation.error_message = (
            result.get("detail")
            or "Could not create Meshy task."
        )

        generation.save(
            update_fields=[
                "status",
                "error_message",
            ]
        )

        return Response(
            {
                "status": "error",
                "generation_id": generation.id,
                "detail": generation.error_message,
            },
            status=status.HTTP_502_BAD_GATEWAY,
        )

    # --------------------------------------------------------
    # Meshy task created successfully
    # --------------------------------------------------------

    generation.meshy_task_id = result.get(
        "task_id"
    )

    if not generation.meshy_task_id:

        generation.status = "failed"

        generation.error_message = (
            "Meshy did not return a task ID."
        )

        generation.save(
            update_fields=[
                "status",
                "error_message",
            ]
        )

        return Response(
            {
                "status": "error",
                "generation_id": generation.id,
                "detail": generation.error_message,
            },
            status=status.HTTP_502_BAD_GATEWAY,
        )

    generation.status = "processing"
    generation.error_message = None

    generation.save(
        update_fields=[
            "meshy_task_id",
            "status",
            "error_message",
        ]
    )

    return Response(
        {
            "status": "processing",
            "generation_id": generation.id,
            "meshy_task_id": generation.meshy_task_id,
        },
        status=status.HTTP_202_ACCEPTED,
    )


# ============================================================
# CHECK 3D GENERATION STATUS
# ============================================================

@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def check_3d_status(
    request,
    generation_id,
):

    # --------------------------------------------------------
    # Find generation
    # --------------------------------------------------------

    try:
        generation = ThreeDGeneration.objects.get(
            id=generation_id
        )

    except ThreeDGeneration.DoesNotExist:

        return Response(
            {
                "status": "error",
                "detail": "3D generation not found.",
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    # ========================================================
    # ALREADY COMPLETED
    # ========================================================

    if generation.status == "succeeded":

        # ----------------------------------------------------
        # IMPORTANT:
        # Always prefer our locally stored GLB.
        # ----------------------------------------------------

        if generation.model_file:

            try:
                local_model_url = request.build_absolute_uri(
                    generation.model_file.url
                )

                return Response(
                    {
                        "status": "succeeded",
                        "generation_id": generation.id,
                        "meshy_task_id": generation.meshy_task_id,
                        "progress": 100,
                        "model_url": local_model_url,
                        "error_message": None,
                    }
                )

            except Exception:
                pass

        # ----------------------------------------------------
        # Old generation:
        # We have Meshy URL but no local file.
        #
        # Download it now so the browser never accesses
        # assets.meshy.ai directly.
        # ----------------------------------------------------

        if generation.model_url:

            save_result = save_meshy_model_locally(
                generation,
                generation.model_url
            )

            if save_result["success"]:

                try:
                    local_model_url = request.build_absolute_uri(
                        generation.model_file.url
                    )

                except Exception:
                    local_model_url = None

                return Response(
                    {
                        "status": "succeeded",
                        "generation_id": generation.id,
                        "meshy_task_id": generation.meshy_task_id,
                        "progress": 100,
                        "model_url": local_model_url,
                        "error_message": None,
                    }
                )

            generation.status = "failed"
            generation.error_message = (
                save_result["error"]
            )

            generation.save(
                update_fields=[
                    "status",
                    "error_message",
                ]
            )

            return Response(
                {
                    "status": "failed",
                    "generation_id": generation.id,
                    "meshy_task_id": generation.meshy_task_id,
                    "progress": 100,
                    "model_url": None,
                    "error_message": generation.error_message,
                }
            )

    # ========================================================
    # NO MESHY TASK
    # ========================================================

    if not generation.meshy_task_id:

        return Response(
            {
                "status": generation.status,
                "generation_id": generation.id,
                "meshy_task_id": None,
                "progress": 0,
                "model_url": None,
                "error_message": (
                    "Meshy task has not started."
                ),
            }
        )

    # ========================================================
    # CHECK MESHY
    # ========================================================

    try:

        result = get_meshy_task(
            generation.meshy_task_id
        )

    except Exception as e:

        return Response(
            {
                "status": "error",
                "generation_id": generation.id,
                "meshy_task_id": generation.meshy_task_id,
                "progress": 0,
                "model_url": None,
                "error_message": str(e),
            },
            status=status.HTTP_502_BAD_GATEWAY,
        )

    # --------------------------------------------------------
    # Meshy API error
    # --------------------------------------------------------

    if result.get("error"):

        return Response(
            {
                "status": "error",
                "generation_id": generation.id,
                "meshy_task_id": generation.meshy_task_id,
                "progress": 0,
                "model_url": None,
                "error_message": (
                    result.get("detail")
                    or "Could not check Meshy task."
                ),
            },
            status=status.HTTP_502_BAD_GATEWAY,
        )

    data = result.get("data") or {}

    meshy_status = data.get(
        "status"
    )

    progress = data.get(
        "progress",
        0,
    )

    # ========================================================
    # MESHY SUCCEEDED
    # ========================================================

    if meshy_status == "SUCCEEDED":

        model_urls = data.get(
            "model_urls"
        ) or {}

        glb_url = model_urls.get(
            "glb"
        )

        # ----------------------------------------------------
        # No GLB URL returned
        # ----------------------------------------------------

        if not glb_url:

            generation.status = "failed"

            generation.error_message = (
                "Meshy succeeded but no GLB "
                "model URL was returned."
            )

            generation.save(
                update_fields=[
                    "status",
                    "error_message",
                ]
            )

            return Response(
                {
                    "status": "failed",
                    "generation_id": generation.id,
                    "meshy_task_id": generation.meshy_task_id,
                    "progress": 100,
                    "model_url": None,
                    "error_message": (
                        generation.error_message
                    ),
                }
            )

        # ----------------------------------------------------
        # DOWNLOAD GLB FROM MESHY
        # ----------------------------------------------------

        save_result = save_meshy_model_locally(
            generation,
            glb_url
        )

        if not save_result["success"]:

            generation.status = "failed"

            generation.error_message = (
                save_result["error"]
            )

            generation.save(
                update_fields=[
                    "status",
                    "error_message",
                ]
            )

            return Response(
                {
                    "status": "failed",
                    "generation_id": generation.id,
                    "meshy_task_id": generation.meshy_task_id,
                    "progress": 100,
                    "model_url": None,
                    "error_message": (
                        generation.error_message
                    ),
                }
            )

        # ----------------------------------------------------
        # BUILD OUR BACKEND URL
        # ----------------------------------------------------

        try:
            local_model_url = request.build_absolute_uri(
                generation.model_file.url
            )

        except Exception as exc:

            generation.status = "failed"
            generation.error_message = (
                "GLB was saved, but the local model URL "
                f"could not be created: {str(exc)}"
            )

            generation.save(
                update_fields=[
                    "status",
                    "error_message",
                ]
            )

            return Response(
                {
                    "status": "failed",
                    "generation_id": generation.id,
                    "meshy_task_id": generation.meshy_task_id,
                    "progress": 100,
                    "model_url": None,
                    "error_message": (
                        generation.error_message
                    ),
                }
            )

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        return Response(
            {
                "status": "succeeded",
                "generation_id": generation.id,
                "meshy_task_id": generation.meshy_task_id,
                "progress": 100,

                # IMPORTANT:
                # This is OUR backend URL, NOT Meshy's URL.
                "model_url": local_model_url,

                "error_message": None,
            }
        )

    # ========================================================
    # MESHY FAILED
    # ========================================================

    if meshy_status in [
        "FAILED",
        "CANCELED",
    ]:

        generation.status = "failed"

        task_error = (
            data.get("task_error")
            or {}
        )

        generation.error_message = (
            task_error.get("message")
            or task_error.get("detail")
            or (
                f"Meshy task ended with status: "
                f"{meshy_status}"
            )
        )

        generation.save(
            update_fields=[
                "status",
                "error_message",
            ]
        )

        return Response(
            {
                "status": "failed",
                "generation_id": generation.id,
                "meshy_task_id": generation.meshy_task_id,
                "progress": progress,
                "model_url": None,
                "error_message": (
                    generation.error_message
                ),
            }
        )

    # ========================================================
    # STILL PROCESSING
    # ========================================================

    generation.status = "processing"

    generation.save(
        update_fields=[
            "status",
        ]
    )

    return Response(
        {
            "status": "processing",
            "generation_id": generation.id,
            "meshy_task_id": generation.meshy_task_id,
            "progress": progress,
            "model_url": None,
            "error_message": None,
        }
    )