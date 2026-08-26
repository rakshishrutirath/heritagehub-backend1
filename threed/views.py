from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import ThreeDGeneration
from .services import (
    create_meshy_task,
    get_meshy_task,
)


# ============================================================
# GENERATE 3D MODEL FROM IMAGE
# ============================================================

@api_view(["POST"])
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

    generation = ThreeDGeneration.objects.create(
        image=image,
        status="pending",
    )

    # --------------------------------------------------------
    # Send image to Meshy
    # --------------------------------------------------------

    result = create_meshy_task(
        generation.image
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

        generation.save()

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

    generation.status = "processing"

    generation.error_message = None

    generation.save()

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

        model_url = None

        # Prefer Meshy URL
        if generation.model_url:
            model_url = generation.model_url

        # Fallback to stored file
        elif generation.model_file:

            try:
                model_url = request.build_absolute_uri(
                    generation.model_file.url
                )
            except Exception:
                model_url = None

        return Response(
            {
                "status": "succeeded",
                "generation_id": generation.id,
                "meshy_task_id": generation.meshy_task_id,
                "progress": 100,
                "model_url": model_url,
                "error_message": None,
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

    result = get_meshy_task(
        generation.meshy_task_id
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

            generation.save()

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

        # ====================================================
        # IMPORTANT
        #
        # DO NOT DOWNLOAD THE GLB.
        #
        # Your previous code downloaded the GLB and tried
        # to save it to Cloudinary. Your GLB was ~77 MB,
        # while Cloudinary rejected files above 10 MB.
        #
        # We therefore keep Meshy's GLB URL directly.
        # ====================================================

        generation.model_url = glb_url

        generation.status = "succeeded"

        generation.error_message = None

        generation.save(
            update_fields=[
                "model_url",
                "status",
                "error_message",
            ]
        )

        return Response(
            {
                "status": "succeeded",
                "generation_id": generation.id,
                "meshy_task_id": generation.meshy_task_id,
                "progress": 100,
                "model_url": glb_url,
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

        generation.save()

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