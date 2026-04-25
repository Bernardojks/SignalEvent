from celery import shared_task

from apps.analysis.models import AnalysisJob
from apps.analysis.services import process_analysis_job


@shared_task
def process_analysis_job_task(job_id: int):
    job = AnalysisJob.objects.select_related("submission").get(id=job_id)
    process_analysis_job(job)