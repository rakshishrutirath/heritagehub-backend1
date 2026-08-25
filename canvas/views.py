from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import CanvasArtwork
from .serializers import CanvasArtworkSerializer


@api_view(['POST'])
def save_canvas_artwork(request):

    serializer = CanvasArtworkSerializer(data=request.data)

    if serializer.is_valid():
        artwork = serializer.save()

        return Response(
            CanvasArtworkSerializer(
                artwork,
                context={'request': request}
            ).data,
            status=status.HTTP_201_CREATED
        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )


@api_view(['GET'])
def canvas_artworks(request):

    artworks = CanvasArtwork.objects.all().order_by('-created_at')

    serializer = CanvasArtworkSerializer(
        artworks,
        many=True,
        context={'request': request}
    )

    return Response(serializer.data)