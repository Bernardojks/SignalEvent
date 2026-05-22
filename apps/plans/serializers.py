from rest_framework import serializers

from apps.plans.models import Plan


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = [
            "id",
            "name",
            "code",
            "monthly_analysis_limit",
        ]


class PlanChangeSerializer(serializers.Serializer):
    plan_code = serializers.CharField()

    def validate_plan_code(self, value):
        if not Plan.objects.filter(code=value).exists():
            raise serializers.ValidationError("Plan does not exist.")
        return value
