from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Quote
from .serializers import QuoteSerializer

class QuoteViewSet(viewsets.ModelViewSet):
    serializer_class = QuoteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name__in=['Finance', 'Admin']).exists():
            return Quote.objects.all().select_related('customer', 'delivery_location').prefetch_related('items')
        return user.quotes.all().select_related('customer', 'delivery_location').prefetch_related('items')

    @action(detail=True, methods=['post'])
    def mark_quoted(self, request, pk=None):
        quote = self.get_object()
        quote.status = Quote.Status.QUOTED
        quote.save()
        return Response({'status': 'Quote marked as quoted'})

    @action(detail=True, methods=['post'])
    def mark_accepted(self, request, pk=None):
        quote = self.get_object()
        quote.status = Quote.Status.ACCEPTED
        quote.save()
        return Response({'status': 'Quote accepted'})

    @action(detail=True, methods=['post'])
    def mark_rejected(self, request, pk=None):
        quote = self.get_object()
        quote.status = Quote.Status.REJECTED
        quote.save()
        return Response({'status': 'Quote rejected'})
