from django.shortcuts import get_object_or_404

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.dashboard.serializers import DashboardOverviewQuerySerializer
from apps.dashboard.selectors import get_dashboard_overview, get_form_analytics
from apps.forms.models import FeedbackForm


class DashboardOverviewAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        organization = request.user.organization

        if not organization:
            return Response({"detail": "No organization found."}, status=404)

        query_serializer = DashboardOverviewQuerySerializer(
            data=request.query_params.dict()
        )
        query_serializer.is_valid(raise_exception=True)
        filters = dict(query_serializer.validated_data)

        form_id = filters.pop("form_id", None)
        if form_id is not None:
            filters["form"] = get_object_or_404(
                FeedbackForm,
                id=form_id,
                organization=organization,
            )

        data = get_dashboard_overview(organization, filters=filters)
        return Response(data)


class FormAnalyticsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, form_id):
        form = get_object_or_404(
            FeedbackForm,
            id=form_id,
            organization=request.user.organization,
        )

        data = get_form_analytics(form)
        return Response(data)
