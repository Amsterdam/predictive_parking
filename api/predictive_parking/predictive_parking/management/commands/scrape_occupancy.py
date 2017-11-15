"""
Import commands
"""

import logging
# import sys

from django.core.management import BaseCommand
from django.conf import settings

from occupancy import scrape_api

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Load occupancy data from API.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '--wegdelen',
            action='store_true',
            dest='wegdelen',
            default=False,
            help='importeer wegdelen uit bgt')

        parser.add_argument(
            '--selections',
            action='store_true',
            dest='selections',
            default=False,
            help='bouw de mogelijke selecties')

        parser.add_argument(
            '--part',
            action='store',
            dest='part',
            default=0,
            help='part X of 4')

        parser.add_argument(
            '--addselection',
            action='store',
            dest='newselection',
            default=0,
            help='selection == yyyy:yyyy:mm:mm:dd:dd:hh:hh')

        parser.add_argument(
            '--create_views',
            action='store_true',
            dest='createviews',
            default=False,
            help='create occupancy views',
        )

        parser.add_argument(
            '--dumpcsv',
            action='store_true',
            dest='dumpcsv',
            default=False,
            help='dump csv views',
        )

    def handle(self, *args, **options):
        """
        Scrape occupancy table to fill
        """
        if options['part']:
            part = int(options['part'])
            assert 0 < part < 5
            settings.SCRAPE['IMPORT_PART'] = part

        if options['newselection']:
            scrape_api.create_single_selection(options['newselection'])

        if options['createviews']:
            scrape_api.create_selection_views()

        if options['wegdelen']:
            scrape_api.fill_occupancy_roadparts()

        if options['selections']:
            scrape_api.create_selection_buckets()

        if options['dumpcsv']:
            scrape_api.dump_csv_files()
