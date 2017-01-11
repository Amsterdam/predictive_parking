"""
Modify scan data so we can work with it.
Importing is done with a golang script
into the scan_scan table
"""

import logging

# from collections import OrderedDict
# from django.conf import settings
from django.db import connection
# rom django.db.utils import DataError

from scans.models import WegDeel
from scans.models import Parkeervak

from logdecorator import LogWith


logging.basicConfig(level=logging.DEBUG)

log = logging.getLogger(__name__)


@LogWith(log)
def set_geometrie_field():
    """
    Convert the lat - long fields to geometry

    Done in golang.

    takes 40 mins.
    """

    log.debug('Set field geometry..')
    with connection.cursor() as c:
        c.execute("""
    UPDATE scans_scan
    SET geometrie = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
    """)


#@LogWith(log)
#def set_geometrie_rd_field():
#    """
#    NOT used. We convert Parkeervakken / Wegdelen naar 4326
#    """
#    log.debug('Convert field geometry RD')
#    with connection.cursor() as c:
#            c.execute("""
#    UPDATE scans_scan
#    SET geometrie_rd = ST_Transform(geometrie, 28992)
#        """)


@LogWith(log)
def fix_pv_geometrie_field():
    """
    Add 4326 field to parkeervakken
    """
    log.debug('Convert field geometry 4326')
    with connection.cursor() as c:
            c.execute("""
    ALTER TABLE bv.parkeervakken
    ADD COLUMN geomw geometry(MULTIPOLYGON, 4326)
    """)
            c.execute("""
    UPDATE bv.parkeervakken
    SET geomw=ST_Transform(geom, 4326)
    """)


@LogWith(log)
def fix_bgt_geometrie_field():
    """
    Add 4326 field to parkeervakken
    """
    log.debug('Convert field geometry 4326')
    with connection.cursor() as c:
            c.execute("""
    ALTER TABLE bgt.bgt_wegdeel
    ADD COLUMN geomw geometry(CurvePolygon, 4326)
    """)
            c.execute("""
    UPDATE bgt.bgt_wegdeel
    SET geomw=ST_Transform(geometrie, 4326)
    """)


@LogWith(log)
def add_parkeervak_to_scans():
    """
    Given scans pind nearest parking spot
    """
    log.debug('Add parkeervak to each scan (40 mins)')
    with connection.cursor() as c:
        c.execute("""
    UPDATE scans_scan s
    SET
        parkeervak_id       = pv.id,
        parkeervak_soort    = pv.soort,
        bgt_wegdeel         = pv.bgt_wegdeel,
        bgt_wegdeel_functie = pv.bgt_wegdeel_functie
    FROM scans_parkeervak pv
    WHERE ST_DWithin(s.geometrie, pv.geometrie, 0.000015)
    """)


@LogWith(log)
def add_wegdeel_to_parkeervak():
    """
    Each parking spot should have a wegdeel
    """
    log.debug('Add wegdeel to each parking spot')
    with connection.cursor() as c:
        c.execute("""
    UPDATE scans_parkeervak pv
    SET bgt_wegdeel = wd.id, bgt_wegdeel_functie = wd.bgt_functie
    FROM scans_wegdeel wd
    WHERE ST_DWithin(wd.geometrie, pv.geometrie, 0.000049)
    """)

    count = (
        Parkeervak.objects
        .filter(bgt_wegdeel=None)
        .filter(soort="FISCAAL")
        .count())
    log.debug("Fiscale Parkeervakken zonder WegDeel %s", count)


@LogWith(log)
def import_parkeervakken():
    log.debug('Import en Converteer parkeervakken naar WGS84')
    Parkeervak.objects.all().delete()
    with connection.cursor() as c:
        c.execute("""
    INSERT INTO scans_parkeervak(
        id,
        straatnaam,
        soort,
        type,
        aantal,
        geometrie)
    SELECT
        parkeer_id,
        straatnaam,
        soort,
        type,
        aantal,
        ST_Transform(ST_SetSRID(geom, 28992), 4326)
    FROM bv.parkeervakken pv
    """)


@LogWith(log)
def import_wegdelen():
    log.debug('Import en Converteer wegdelen naar WGS84 Polygonen')

    WegDeel.objects.all().delete()

    with connection.cursor() as c:
        c.execute("""
    INSERT INTO scans_wegdeel(
        id,
        bgt_functie,
        geometrie
    )
    SELECT
        identificatie_lokaalid,
        bgt_functie,
        ST_CurveToLine(ST_Transform(ST_SetSRID(geometrie, 28992), 4326))
    FROM bgt.bgt_wegdeel wg
    WHERE
        wg.bgt_functie LIKE 'rijbaan lokale weg' OR
        wg.bgt_functie LIKE 'rijbaan regionale weg' OR
        wg.bgt_functie LIKE 'transitie' OR
        wg.bgt_functie LIKE 'OV-baan' OR
        wg.bgt_functie LIKE 'woonerf' OR
        wg.bgt_functie LIKE 'parkeervlak'

    """)


@LogWith(log)
def add_wegdeel_to_scans():
    """
    Given scans find nearest parking spot
    within 1.5 meters
    """
    log.debug('Add wegdeel to each parkeervak (1 min)')
    with connection.cursor() as c:
        c.execute("""
    UPDATE  s
    SET wegvak_id = wd.identificatie_lokaalid
    FROM bgt.bgt_wegdeel wd
    WHERE ST_DWithin(s.geometrie, pv.geomw, 0.000015)
    """)