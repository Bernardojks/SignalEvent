from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.plans.selectors import get_current_subscription_data, list_available_plans
from apps.plans.serializers import PlanChangeSerializer, PlanSerializer
from apps.plans.services import cancel_subscription, change_subscription_plan
from apps.plans.models import Plan


def build_subscription_response(data):
    serializer = PlanSerializer(data["subscription"]["plan"]) if data["subscription"] else None

    response_data = {
        "subscription": None,
        "usage": data["usage"],
    }

    if data["subscription"]:
        response_data["subscription"] = {
            "id": data["subscription"]["id"],
            "active": data["subscription"]["active"],
            "current_period_start": data["subscription"]["current_period_start"],
            "current_period_end": data["subscription"]["current_period_end"],
            "plan": serializer.data,
        }

    return response_data


class PlanListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = PlanSerializer(list_available_plans(), many=True)
        return Response(serializer.data)


class CurrentSubscriptionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        organization = request.user.organization

        if not organization:
            return Response(
                {
                    "subscription": None,
                    "usage": None,
                }
            )

        data = get_current_subscription_data(organization)
        return Response(build_subscription_response(data))


class ChangeCurrentPlanAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        organization = request.user.organization
        if not organization:
            return Response(
                {"detail": "Authenticated user has no organization."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = PlanChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        plan = Plan.objects.get(code=serializer.validated_data["plan_code"])

        try:
            change_subscription_plan(organization, plan)
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = get_current_subscription_data(organization)
        return Response(build_subscription_response(data))


class CancelCurrentPlanAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        organization = request.user.organization
        if not organization:
            return Response(
                {"detail": "Authenticated user has no organization."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            cancel_subscription(organization)
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = get_current_subscription_data(organization)
        return Response(build_subscription_response(data))
