import logging
import requests

from django.core.files.base import ContentFile
from django.http import JsonResponse

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import ThreeDGeneration
from .services import create_meshy_task, get_meshy_task


logger = logging.getLogger(__name__)


# ============================================================
# CREATE 3D GENERATION
# ============================================================

@api_view(["POST"])
def generate_3d_from_image(request):

    try:
        # ----------------------------------------------------
        # Get uploaded image
        # ----------------------------------------------------

        image = request.FILES.get("image")

        if not image:
            return Response(
                {
                    "status": "error",
                    "detail": "Please upload an image."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ----------------------------------------------------
        # Create database record
        # ----------------------------------------------------

        generation = ThreeDGeneration.objects.create(
            image=image,
            status="pending"
        )

        logger.info(
            "Created 3D generation: %s",
            generation.id
        )

        # ----------------------------------------------------
        # Send image to Meshy
        # ----------------------------------------------------

        result = create_meshy_task(
            generation.image
        )

        # ----------------------------------------------------
        # Meshy API error
        # ----------------------------------------------------

        if result.get("error"):

            generation.status = "failed"
            generation.error_message = result.get(
                "detail",
                "Unknown Meshy error."
            )

            generation.save(
                update_fields=[
                    "status",
                    "error_message"
                ]
            )

            logger.error(
                "Meshy create task failed for %s: %s",
                generation.id,
                generation.error_message
            )

            return Response(
                {
                    "status": "error",
                    "generation_id": generation.id,
                    "detail": generation.error_message
                },
                status=status.HTTP_502_BAD_GATEWAY
            )

        # ----------------------------------------------------
        # Get Meshy task ID
        # ----------------------------------------------------

        task_id = result.get("task_id")

        if not task_id:

            generation.status = "failed"
            generation.error_message = (
                "Meshy did not return a task ID."
            )

            generation.save(
                update_fields=[
                    "status",
                    "error_message"
                ]
            )

            return Response(
                {
                    "status": "error",
                    "generation_id": generation.id,
                    "detail": generation.error_message
                },
                status=status.HTTP_502_BAD_GATEWAY
            )

        # ----------------------------------------------------
        # Save Meshy task
        # ----------------------------------------------------

        generation.meshy_task_id = task_id
        generation.status = "processing"

        generation.save(
            update_fields=[
                "meshy_task_id",
                "status"
            ]
        )

        logger.info(
            "Meshy task started. Generation=%s Task=%s",
            generation.id,
            task_id
        )

        # ----------------------------------------------------
        # Return response
        # ----------------------------------------------------

        return Response(
            {
                "status": "processing",
                "generation_id": generation.id,
                "meshy_task_id": generation.meshy_task_id,
                "progress": 0,
                "model_url": None,
                "error_message": None
            },
            status=status.HTTP_202_ACCEPTED
        )

    except Exception as exc:

        logger.exception(
            "Unexpected error while creating 3D generation."
        )

        return Response(
            {
                "status": "error",
                "detail": (
                    "Unexpected server error while "
                    "starting 3D generation."
                ),
                "error": str(exc)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================================
# CHECK 3D GENERATION STATUS
# ============================================================

@api_view(["GET"])
def check_3d_status(request, generation_id):

    try:

        # ----------------------------------------------------
        # Find generation
        # ----------------------------------------------------

        try:

            generation = ThreeDGeneration.objects.get(
                id=generation_id
            )

        except ThreeDGeneration.DoesNotExist:

            return Response(
                {
                    "status": "error",
                    "detail": "3D generation not found.",
                    "generation_id": generation_id
                },
                status=status.HTTP_404_NOT_FOUND
            )

        logger.info(
            "Checking 3D status. Generation=%s",
            generation.id
        )

        # ----------------------------------------------------
        # Already successfully downloaded
        # ----------------------------------------------------

        if (
            generation.status == "succeeded"
            and generation.model_file
        ):

            try:

                permanent_url = request.build_absolute_uri(
                    generation.model_file.url
                )

            except Exception as exc:

                logger.exception(
                    "Could not build model URL."
                )

                permanent_url = None

            return Response(
                {
                    "status": "succeeded",
                    "generation_id": generation.id,
                    "meshy_task_id": generation.meshy_task_id,
                    "progress": 100,
                    "model_url": permanent_url,
                    "error_message": None
                },
                status=status.HTTP_200_OK
            )

        # ----------------------------------------------------
        # Meshy task hasn't started
        # ----------------------------------------------------

        if not generation.meshy_task_id:

            return Response(
                {
                    "status": generation.status,
                    "generation_id": generation.id,
                    "meshy_task_id": None,
                    "progress": 0,
                    "model_url": None,
                    "error_message": generation.error_message,
                    "detail": "Meshy task has not started."
                },
                status=status.HTTP_200_OK
            )

        # ----------------------------------------------------
        # Ask Meshy for current status
        # ----------------------------------------------------

        result = get_meshy_task(
            generation.meshy_task_id
        )

        # ----------------------------------------------------
        # Meshy API error
        # ----------------------------------------------------

        if result.get("error"):

            logger.error(
                "Meshy status request failed. "
                "Generation=%s Task=%s Error=%s",
                generation.id,
                generation.meshy_task_id,
                result.get("detail")
            )

            return Response(
                {
                    "status": "error",
                    "generation_id": generation.id,
                    "meshy_task_id": generation.meshy_task_id,
                    "detail": result.get(
                        "detail",
                        "Could not get Meshy status."
                    )
                },
                status=status.HTTP_502_BAD_GATEWAY
            )

        # ----------------------------------------------------
        # Get Meshy data
        # ----------------------------------------------------

        data = result.get("data") or {}

        meshy_status = data.get("status")

        progress = data.get(
            "progress",
            0
        )

        # Make sure progress is valid
        try:
            progress = int(progress)
        except (TypeError, ValueError):
            progress = 0

        progress = max(
            0,
            min(progress, 100)
        )

        logger.info(
            "Meshy status. Generation=%s Status=%s Progress=%s",
            generation.id,
            meshy_status,
            progress
        )

        # ====================================================
        # MESHY SUCCESS
        # ====================================================

        if meshy_status == "SUCCEEDED":

            model_urls = data.get(
                "model_urls"
            ) or {}

            glb_url = model_urls.get(
                "glb"
            )

            # ------------------------------------------------
            # No GLB URL
            # ------------------------------------------------

            if not glb_url:

                generation.status = "failed"

                generation.error_message = (
                    "Meshy succeeded but no GLB model URL "
                    "was returned."
                )

                generation.save(
                    update_fields=[
                        "status",
                        "error_message"
                    ]
                )

                logger.error(
                    "Meshy succeeded without GLB URL. "
                    "Generation=%s",
                    generation.id
                )

                return Response(
                    {
                        "status": "failed",
                        "generation_id": generation.id,
                        "meshy_task_id": generation.meshy_task_id,
                        "progress": 100,
                        "model_url": None,
                        "error_message": generation.error_message
                    },
                    status=status.HTTP_200_OK
                )

            # ------------------------------------------------
            # Save original Meshy URL
            # ------------------------------------------------

            generation.model_url = glb_url

            # ------------------------------------------------
            # Download GLB if not already stored
            # ------------------------------------------------

            if not generation.model_file:

                try:

                    logger.info(
                        "Downloading GLB model for generation %s",
                        generation.id
                    )

                    glb_response = requests.get(
                        glb_url,
                        timeout=120
                    )

                    glb_response.raise_for_status()

                    # ----------------------------------------
                    # Make filename
                    # ----------------------------------------

                    filename = (
                        f"{generation.id}.glb"
                    )

                    # ----------------------------------------
                    # Save model
                    # ----------------------------------------

                    generation.model_file.save(
                        filename,
                        ContentFile(
                            glb_response.content
                        ),
                        save=False
                    )

                    generation.status = "succeeded"
                    generation.error_message = None

                    generation.save()

                    logger.info(
                        "GLB successfully saved. "
                        "Generation=%s",
                        generation.id
                    )

                except requests.RequestException as exc:

                    generation.status = "failed"

                    generation.error_message = (
                        "3D model was generated, but Django "
                        "could not download the GLB file: "
                        f"{str(exc)}"
                    )

                    generation.save(
                        update_fields=[
                            "model_url",
                            "status",
                            "error_message"
                        ]
                    )

                    logger.exception(
                        "Failed to download GLB."
                    )

                except Exception as exc:

                    generation.status = "failed"

                    generation.error_message = (
                        "3D model was generated, but Django "
                        "could not save the GLB file: "
                        f"{str(exc)}"
                    )

                    generation.save(
                        update_fields=[
                            "model_url",
                            "status",
                            "error_message"
                        ]
                    )

                    logger.exception(
                        "Failed to save GLB."
                    )

            # ------------------------------------------------
            # Already stored
            # ------------------------------------------------

            else:

                generation.status = "succeeded"
                generation.error_message = None

                generation.save(
                    update_fields=[
                        "model_url",
                        "status",
                        "error_message"
                    ]
                )

        # ====================================================
        # MESHY FAILED / CANCELED
        # ====================================================

        elif meshy_status in [
            "FAILED",
            "CANCELED"
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
                    "error_message"
                ]
            )

            logger.error(
                "Meshy generation failed. "
                "Generation=%s Status=%s Error=%s",
                generation.id,
                meshy_status,
                generation.error_message
            )

        # ====================================================
        # STILL PROCESSING
        # ====================================================

        else:

            generation.status = "processing"

            generation.save(
                update_fields=[
                    "status"
                ]
            )

        # ====================================================
        # BUILD PERMANENT MODEL URL
        # ====================================================

        permanent_url = None

        if generation.model_file:

            try:

                permanent_url = request.build_absolute_uri(
                    generation.model_file.url
                )

            except Exception as exc:

                logger.exception(
                    "Could not generate permanent model URL."
                )

                permanent_url = None

        # ====================================================
        # FINAL RESPONSE
        # ====================================================

        return Response(
            {
                "status": generation.status,
                "generation_id": generation.id,
                "meshy_task_id": generation.meshy_task_id,
                "progress": progress,
                "model_url": permanent_url,
                "error_message": generation.error_message
            },
            status=status.HTTP_200_OK
        )

    # ========================================================
    # GLOBAL ERROR HANDLER
    # ========================================================

    except Exception as exc:

        logger.exception(
            "Unexpected error while checking 3D status. "
            "Generation=%s",
            generation_id
        )

        return Response(
            {
                "status": "error",
                "generation_id": generation_id,
                "detail": (
                    "Unexpected server error while "
                    "checking 3D generation status."
                ),
                "error": str(exc)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )