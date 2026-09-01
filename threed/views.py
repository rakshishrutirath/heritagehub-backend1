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
        # Return the Meshy URL directly.
        #
        # DO NOT download the GLB on PythonAnywhere.
        # ----------------------------------------------------

        if generation.model_url:

            return Response(
                {
                    "status": "succeeded",
                    "generation_id": generation.id,
                    "meshy_task_id": generation.meshy_task_id,
                    "progress": 100,
                    "model_url": generation.model_url,
                    "error_message": None,
                }
            )

        return Response(
            {
                "status": "failed",
                "generation_id": generation.id,
                "meshy_task_id": generation.meshy_task_id,
                "progress": 100,
                "model_url": None,
                "error_message": (
                    "Generation succeeded but no "
                    "Meshy model URL is available."
                ),
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
        # IMPORTANT:
        #
        # DO NOT DOWNLOAD THE GLB HERE.
        #
        # PythonAnywhere was getting:
        #
        # ProxyError
        # Tunnel connection failed: 403 Forbidden
        #
        # Instead, save only the Meshy URL.
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        return Response(
            {
                "status": "succeeded",
                "generation_id": generation.id,
                "meshy_task_id": generation.meshy_task_id,
                "progress": 100,

                # This is the Meshy URL.
                # Frontend will pass this URL through
                # /api/meshy-model.js
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