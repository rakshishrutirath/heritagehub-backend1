# ============================================================
# threed/views.py
# ============================================================

from django.core.files.base import ContentFile

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import ThreeDGeneration
from .services import (
    create_meshy_task,
    get_meshy_task,
    download_glb,
)


# ============================================================
# GENERATE 3D MODEL FROM IMAGE
# ============================================================

@api_view(["POST"])
def generate_3d_from_image(request):

    # --------------------------------------------------------
    # Get uploaded image
    # --------------------------------------------------------

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
    # Meshy task creation failed
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
    # Get Meshy task ID
    # --------------------------------------------------------

    task_id = result.get("task_id")

    if not task_id:

        generation.status = "failed"

        generation.error_message = (
            "Meshy did not return a task ID."
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
    # Save Meshy task
    # --------------------------------------------------------

    generation.meshy_task_id = task_id
    generation.status = "processing"

    generation.save()

    # --------------------------------------------------------
    # Return processing response
    # --------------------------------------------------------

    return Response(
        {
            "status": "processing",
            "generation_id": generation.id,
            "meshy_task_id": generation.meshy_task_id,
            "progress": 0,
            "model_url": None,
            "error_message": None,
        },
        status=status.HTTP_202_ACCEPTED,
    )


# ============================================================
# CHECK 3D GENERATION STATUS
# ============================================================

@api_view(["GET"])
def check_3d_status(request, generation_id):

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
    # ALREADY SUCCESSFULLY STORED
    # ========================================================

    if (
        generation.status == "succeeded"
        and generation.model_file
    ):

        permanent_url = request.build_absolute_uri(
            generation.model_file.url
        )

        return Response(
            {
                "status": "succeeded",
                "generation_id": generation.id,
                "meshy_task_id": generation.meshy_task_id,
                "progress": 100,
                "model_url": permanent_url,
                "error_message": None,
            }
        )

    # ========================================================
    # MESHY TASK DOES NOT EXIST
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
    # ASK MESHY FOR STATUS
    # ========================================================

    result = get_meshy_task(
        generation.meshy_task_id
    )

    # --------------------------------------------------------
    # Meshy request failed
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

    # --------------------------------------------------------
    # Get Meshy response data
    # --------------------------------------------------------

    data = result.get("data") or {}

    meshy_status = data.get("status")

    progress = data.get(
        "progress",
        0
    )

    # ========================================================
    # MESHY SUCCEEDED
    # ========================================================

    if meshy_status == "SUCCEEDED":

        # ----------------------------------------------------
        # Get model URLs
        # ----------------------------------------------------

        model_urls = data.get(
            "model_urls"
        ) or {}

        glb_url = model_urls.get(
            "glb"
        )

        # ----------------------------------------------------
        # Meshy succeeded but no GLB
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

        # ----------------------------------------------------
        # Save original Meshy URL
        # ----------------------------------------------------

        generation.model_url = glb_url

        # ====================================================
        # DOWNLOAD GLB ONLY ONCE
        # ====================================================

        if not generation.model_file:

            download_result = download_glb(
                glb_url
            )

            # ------------------------------------------------
            # Download failed / file too large
            # ------------------------------------------------

            if download_result.get("error"):

                generation.status = "failed"

                generation.error_message = (
                    download_result.get("detail")
                    or "Could not download GLB model."
                )

                generation.save()

                return Response(
                    {
                        "status": "failed",
                        "generation_id": generation.id,
                        "meshy_task_id": (
                            generation.meshy_task_id
                        ),
                        "progress": 100,
                        "model_url": None,
                        "error_message": (
                            generation.error_message
                        ),
                    }
                )

            # ------------------------------------------------
            # Get downloaded content
            # ------------------------------------------------

            glb_content = download_result.get(
                "content"
            )

            glb_size = download_result.get(
                "size",
                len(glb_content or b"")
            )

            # ------------------------------------------------
            # Extra safety check
            #
            # 10 MB = 10 * 1024 * 1024
            # ------------------------------------------------

            MAX_MODEL_SIZE = (
                10 * 1024 * 1024
            )

            if glb_size > MAX_MODEL_SIZE:

                generation.status = "failed"

                generation.error_message = (
                    "3D model was generated, "
                    "but the GLB file is too large. "
                    f"Got "
                    f"{glb_size} bytes. "
                    f"Maximum is "
                    f"{MAX_MODEL_SIZE} bytes."
                )

                generation.save()

                return Response(
                    {
                        "status": "failed",
                        "generation_id": generation.id,
                        "meshy_task_id": (
                            generation.meshy_task_id
                        ),
                        "progress": 100,
                        "model_url": None,
                        "error_message": (
                            generation.error_message
                        ),
                    }
                )

            # ------------------------------------------------
            # Make sure content exists
            # ------------------------------------------------

            if not glb_content:

                generation.status = "failed"

                generation.error_message = (
                    "Meshy returned an empty GLB file."
                )

                generation.save()

                return Response(
                    {
                        "status": "failed",
                        "generation_id": generation.id,
                        "meshy_task_id": (
                            generation.meshy_task_id
                        ),
                        "progress": 100,
                        "model_url": None,
                        "error_message": (
                            generation.error_message
                        ),
                    }
                )

            # =================================================
            # SAVE GLB TO DJANGO STORAGE
            # =================================================

            filename = (
                f"{generation.id}.glb"
            )

            try:

                generation.model_file.save(
                    filename,
                    ContentFile(
                        glb_content
                    ),
                    save=False,
                )

                generation.status = "succeeded"

                generation.error_message = None

                generation.save()

            except Exception as exc:

                generation.status = "failed"

                generation.error_message = (
                    "3D model was generated, "
                    "but Django could not save "
                    f"the GLB file: {str(exc)}"
                )

                generation.save()

                return Response(
                    {
                        "status": "failed",
                        "generation_id": generation.id,
                        "meshy_task_id": (
                            generation.meshy_task_id
                        ),
                        "progress": 100,
                        "model_url": None,
                        "error_message": (
                            generation.error_message
                        ),
                    }
                )

        # ====================================================
        # MODEL WAS ALREADY STORED
        # ====================================================

        else:

            generation.status = "succeeded"

            generation.error_message = None

            generation.save()

        # ====================================================
        # BUILD PERMANENT MODEL URL
        # ====================================================

        permanent_url = None

        if generation.model_file:

            permanent_url = request.build_absolute_uri(
                generation.model_file.url
            )

        # ====================================================
        # SUCCESS RESPONSE
        # ====================================================

        return Response(
            {
                "status": "succeeded",
                "generation_id": generation.id,
                "meshy_task_id": (
                    generation.meshy_task_id
                ),
                "progress": 100,
                "model_url": permanent_url,
                "error_message": None,
            }
        )

    # ========================================================
    # MESHY FAILED
    # ========================================================

    elif meshy_status in [
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
            or
            task_error.get("detail")
            or
            f"Meshy task ended with status: "
            f"{meshy_status}"
        )

        generation.save()

        return Response(
            {
                "status": "failed",
                "generation_id": generation.id,
                "meshy_task_id": (
                    generation.meshy_task_id
                ),
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

    else:

        generation.status = "processing"

        generation.save()

        return Response(
            {
                "status": "processing",
                "generation_id": generation.id,
                "meshy_task_id": (
                    generation.meshy_task_id
                ),
                "progress": progress,
                "model_url": None,
                "error_message": None,
            }
        )