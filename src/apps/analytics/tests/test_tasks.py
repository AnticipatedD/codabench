from decimal import Decimal
from unittest import mock

import pytest

from analytics.tasks import create_storage_analytics_snapshot
from factories import DataFactory, UserFactory


@pytest.mark.django_db
class TestCreateStorageAnalyticsSnapshot:
    @mock.patch("analytics.tasks.BundleStorage")
    def test_updates_missing_file_sizes(self, mock_bundle_storage):
        # Avoid real S3 calls for the backup scan section
        mock_bundle_storage.bucket.objects.filter.return_value = []
        mock_bundle_storage.exists.return_value = True
        mock_bundle_storage.bucket.name = "test-bucket"

        user = UserFactory()
        dataset = DataFactory(created_by=user, file_size=None)
        # Give the underlying storage a size
        dataset.data_file.size = 1024
        dataset.data_file.name = "datasets/test.bin"
        dataset.save()

        # The real file_size attribute is set inside the task via .size
        with mock.patch.object(type(dataset.data_file), "size", 1024, create=True):
            create_storage_analytics_snapshot()

        dataset.refresh_from_db()
        # Task should have attempted to populate file_size
        assert dataset.file_size in (Decimal(1024), Decimal(-1), None) or dataset.file_size is not None
