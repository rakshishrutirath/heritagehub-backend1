import os
import requests

from django.core.files.base import ContentFile

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import ThreeDGeneration
from .services import create_meshy_task, get_meshy_task


@api_view(['POST'])
def generate_3d_from_image(request):
    image = request.FILES.get('image')

    if not image:
        return Response(
            {
                "status": "error",
                "detail": "Please upload an image."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    generation = ThreeDGeneration.objects.create(
        image=image,
        status='pending'
    )

    result = create_meshy_task(generation.image)

    if result["error"]:
        generation.status = 'failed'
        generation.error_message = result["detail"]
        generation.save()

        return Response(
            {
                "status": "error",
                "detail": result["detail"]
            },
            status=status.HTTP_502_BAD_GATEWAY
        )

    generation.meshy_task_id = result["task_id"]
    generation.status = 'processing'
    generation.save()

    return Response(
        {
            "status": "processing",
            "generation_id": generation.id,
            "meshy_task_id": generation.meshy_task_id
        },
        status=status.HTTP_202_ACCEPTED
    )


@api_view(['GET'])
def check_3d_status(request, generation_id):

    try:
        generation = ThreeDGeneration.objects.get(
            id=generation_id
        )

    except ThreeDGeneration.DoesNotExist:
        return Response(
            {
                "status": "error",
                "detail": "3D generation not found."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    # If we already downloaded and stored the model,
    # don't call Meshy again.
    if generation.status == 'succeeded' and generation.model_file:

        permanent_url = request.build_absolute_uri(
            generation.model_file.url
        )

        return Response({
            "status": "succeeded",
            "generation_id": generation.id,
            "meshy_task_id": generation.meshy_task_id,
            "progress": 100,
            "model_url": permanent_url,
            "error_message": None
        })

    if not generation.meshy_task_id:
        return Response(
            {
                "status": generation.status,
                "detail": "Meshy task has not started."
            }
        )

    result = get_meshy_task(
        generation.meshy_task_id
    )

    if result["error"]:
        return Response(
            {
                "status": "error",
                "detail": result["detail"]
            },
            status=status.HTTP_502_BAD_GATEWAY
        )

    data = result["data"]

    meshy_status = data.get("status")

    # -----------------------------
    # MESHY GENERATION SUCCEEDED
    # -----------------------------

    if meshy_status == "SUCCEEDED":

        model_urls = data.get("model_urls", {})

        glb_url = model_urls.get("glb")

        if not glb_url:
            generation.status = 'failed'
            generation.error_message = (
                "Meshy succeeded but no GLB model URL was returned."
            )
            generation.save()

        else:

            # Keep original Meshy URL as reference
            generation.model_url = glb_url

            # Download only if we haven't already stored it
            if not generation.model_file:

                try:
                    glb_response = requests.get(
                        glb_url,
                        timeout=120
                    )

                    glb_response.raise_for_status()

                    filename = (
                        f"{generation.id}.glb"
                    )

                    generation.model_file.save(
                        filename,
                        ContentFile(glb_response.content),
                        save=False
                    )

                    generation.status = 'succeeded'
                    generation.error_message = None

                except requests.RequestException as exc:

                    generation.status = 'failed'
                    generation.error_message = (
                        f"3D model was generated, "
                        f"but Django could not download "
                        f"the GLB file: {str(exc)}"
                    )

            else:
                generation.status = 'succeeded'
                generation.error_message = None

            generation.save()

    # -----------------------------
    # MESHY GENERATION FAILED
    # -----------------------------

    elif meshy_status in ["FAILED", "CANCELED"]:

        generation.status = 'failed'

        task_error = data.get("task_error") or {}

        generation.error_message = (
            task_error.get("message")
            or f"Meshy task ended with status: {meshy_status}"
        )

        generation.save()

    # -----------------------------
    # STILL GENERATING
    # -----------------------------

    else:

        generation.status = 'processing'

        generation.save()

    # -----------------------------
    # RETURN MODEL
    # -----------------------------

    permanent_url = None

    if generation.model_file:

        permanent_url = request.build_absolute_uri(
            generation.model_file.url
        )

    return Response({
        "status": generation.status,
        "generation_id": generation.id,
        "meshy_task_id": generation.meshy_task_id,
        "progress": data.get("progress", 0),
        "model_url": permanent_url,
        "error_message": generation.error_message
    })
    