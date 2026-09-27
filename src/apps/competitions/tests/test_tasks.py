from unittest import mock

import pytest
from django.core.files.base import ContentFile

from competitions.models import Submission
from competitions.tasks import _send_to_compute_worker
from factories import (
    CompetitionFactory,
    PhaseFactory,
    SubmissionFactory,
    TaskFactory,
    UserFactory,
    QueueFactory,
)


@pytest.mark.django_db
class TestSendToComputeWorker:
    def test_hitl_without_private_queue_marks_failed(self):
        user = UserFactory()
        competition = CompetitionFactory(
            created_by=user,
            enable_human_in_the_loop=True,
            queue=None,
        )
        phase = PhaseFactory(competition=competition)
        task = TaskFactory(created_by=user)
        phase.tasks.add(task)
        submission = SubmissionFactory(
            owner=user,
            phase=phase,
            queue=None,
            status=Submission.SUBMITTING,
        )
        submission.task = task
        submission.save()

        _send_to_compute_worker(submission, is_scoring=False)

        submission.refresh_from_db()
        assert submission.status == Submission.FAILED
        assert "HITL" in (submission.status_details or "")

    @mock.patch("competitions.tasks.transaction.on_commit")
    @mock.patch("competitions.tasks.app.send_task")
    @mock.patch("competitions.tasks.make_url_sassy", return_value="https://example.com/file")
    def test_happy_path_enqueues_task(self, mock_sassy, mock_send_task, mock_on_commit):
        mock_send_task.return_value = mock.Mock(id="celery-task-id")
        # Make on_commit execute the callback immediately
        mock_on_commit.side_effect = lambda fn: fn()

        user = UserFactory()
        competition = CompetitionFactory(created_by=user, enable_human_in_the_loop=False)
        phase = PhaseFactory(competition=competition, execution_time_limit=300)
        task = TaskFactory(created_by=user)
        phase.tasks.add(task)

        submission = SubmissionFactory(
            owner=user,
            phase=phase,
            status=Submission.SUBMITTING,
        )
        submission.task = task
        # Ensure data file exists
        if not submission.data:
            from factories import DataFactory
            submission.data = DataFactory(
                created_by=user,
                type="submission",
                data_file=ContentFile(b"dummy", name="submission.zip"),
            )
        submission.save()

        _send_to_compute_worker(submission, is_scoring=False)

        submission.refresh_from_db()
        assert submission.status == Submission.SUBMITTED
        assert mock_send_task.called
        assert submission.celery_task_id == "celery-task-id"
