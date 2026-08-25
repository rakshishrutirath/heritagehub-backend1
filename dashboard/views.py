from rest_framework.decorators import api_view
from rest_framework.response import Response
from heritage.models import HeritageRecord, Category, Language, Location

@api_view(['GET'])
def impact_stats(request):
    return Response({
        "total_records": HeritageRecord.objects.count(),
        "approved_records": HeritageRecord.objects.filter(status='approved').count(),
        "pending_records": HeritageRecord.objects.filter(status='pending').count(),
        "communities_involved": Location.objects.values('district').distinct().count(),
        "languages_documented": Language.objects.count(),
        "categories_covered": Category.objects.count(),
    })
