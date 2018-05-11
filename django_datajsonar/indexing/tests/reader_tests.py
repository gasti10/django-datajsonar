#! coding: utf-8
import os

from django.test import TestCase
from django.conf import settings

from django_datajsonar.models import Distribution, Field
from django_datajsonar.models import ReadDataJsonTask, Node
from django_datajsonar.indexing.catalog_reader import index_catalog


SAMPLES_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'samples')
CATALOG_ID = 'test_catalog'


class ReaderTests(TestCase):
    catalog = os.path.join(SAMPLES_DIR, 'full_ts_data.json')
    catalog_id = 'catalog_id'

    def setUp(self):
        self.task = ReadDataJsonTask.objects.create()
        self.node = Node(catalog_id=self.catalog_id, catalog_url=self.catalog, indexable=True)
        self.node.save()

    def test_index_same_series_different_catalogs(self):
        index_catalog(self.node, self.task, read_local=True, whitelist=True)
        index_catalog(self.node, self.task, read_local=True, whitelist=True)

        count = Field.objects.filter(metadata__contains='212.1_PSCIOS_ERN_0_0_25').count()

        self.assertEqual(count, 1)

    def test_error_distribution_logs(self):
        catalog = os.path.join(SAMPLES_DIR, 'distribution_missing_downloadurl.json')
        self.node.catalog_url = catalog
        self.node.save()
        index_catalog(self.node, self.task, read_local=True, whitelist=True)

        self.assertGreater(len(ReadDataJsonTask.objects.get(id=self.task.id).logs), 10)

    def test_index_only_time_series_if_specified(self):
        settings.DATAJSON_AR_TIME_SERIES_ONLY = True
        mixed_catalog = os.path.join(SAMPLES_DIR, 'mixed_time_series_catalog.json')
        self.node.catalog_url = mixed_catalog
        self.node.save()
        index_catalog(self.node, self.task, read_local=True, whitelist=True)

        self.assertEqual(Distribution.objects.count(), 2)
        # La distribution ID 5.1 que no es serie de tiempo no fue creada
        self.assertFalse(Distribution.objects.filter(identifier__in=["5.1"]))
