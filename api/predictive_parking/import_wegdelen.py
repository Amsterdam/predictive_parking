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

from wegdelen.models import WegDeel
from wegdelen.models import Parkeervak
# from scans.models import Scan     # Processed scans
# from scans.models import ScanRaw  # Input scans
from wegdelen.models import Buurt

from logdecorator import LogWith


logging.basicConfig(level=logging.DEBUG)

log = logging.getLogger(__name__)


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
def make_scans_unlogged():
    """
    unlogged tables are faster!
    """
    log.debug('Alter table to UNLOGGED')
    with connection.cursor() as c:
            c.execute("""
    ALTER TABLE metingen_scan SET UNLOGGED
    """)
            c.execute("""

    ALTER TABLE metingen_scanraw SET UNLOGGED
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
def cluster_geometrieindexen():
    log.debug('CLUSTER wegdelen takes ~1m')
    with connection.cursor() as c:
        c.execute(f"""
        CLUSTER wegdelen_parkeervak_geometrie_id on wegdelen_parkeervak;
        CLUSTER wegdelen_wegdeel_geometrie_id on wegdelen_wegdeel;
        """)


@LogWith(log)
def scan_moment_index():
    with connection.cursor() as c:
        c.execute(f"""
        CREATE INDEX ON metingen_scan (scan_moment);
        """)


# @LogWith(log)
# def add_parkeervak_to_scans(distance=0.000015):
#    """
#    Given scans pind nearest parking spot
#    """
#    without_parkspot = ScanRaw.objects.filter(parkeervak_id=None).count
#
#    log.debug('Add parkeervak to each scan = (a long time ( ~5 hours))')
#    log.debug('Distance: %.9f', distance)
#    log.debug('Scans: %s', Scan.objects.all().count())
#    log.debug('Scans without parkingspot: %s', without_parkspot())
#
#    with connection.cursor() as c:
#        c.execute(f"""
#    WITH matched_scans AS (
#    DELETE FROM scans_scanraw s
#    USING scans_parkeervak pv
#    WHERE ST_DWithin(s.geometrie, pv.geometrie, {distance})
#    RETURNING
#        s.scan_id,
#        s.scan_moment,
#        s.device_id,
#        s.scan_source,
#        s.longitude,
#        s.latitude,
#        s.buurtcode,
#        s.afstand,
#        s.sperscode,
#        s.qualcode,
#        s.ff_df,
#        s.nha_nr,
#        s.nha_hoogte,
#        s.uitval_nachtrun,
#
#        pv.id,
#        pv.soort,
#        pv.bgt_wegdeel,
#        pv.bgt_wegdeel_functie
#    )
#    INSERT INTO scans_scan(
#        scan_id,
#        scan_moment,
#        device_id,
#        scan_source,
#        longitude,
#        latitude,
#        buurtcode,
#        afstand,
#        sperscode,
#        qualcode,
#        ff_df,
#        nha_nr,
#        nha_hoogte,
#        uitval_nachtrun,
#
#        parkeervak_id,
#        parkeervak_soort,
#        bgt_wegdeel,
#        bgt_wegdeel_functie
#
#        )
#    SELECT * FROM matched_scans;
#
#    """)
#
#    log.debug('Processed Scans: %s', Scan.objects.all().count())
#    log.debug('Scans without parkspot: %s', without_parkspot())


@LogWith(log)
def add_wegdeel_to_parkeervak(distance=0.000049):
    """
    Each parking spot should have a wegdeel
    """
    log.debug('Add wegdeel to each parking spot %.9f', distance)

    with connection.cursor() as c:
        c.execute(f"""
    UPDATE wegdelen_parkeervak pv
    SET bgt_wegdeel = wd.id, bgt_wegdeel_functie = wd.bgt_functie
    FROM wegdelen_wegdeel wd
    WHERE (
        wd.bgt_functie LIKE 'rijbaan lokale weg'
        OR wd.bgt_functie LIKE 'rijbaan regionale weg'
        OR wd.bgt_functie LIKE 'transitie')
    AND
    ST_DWithin(wd.geometrie, pv.geometrie, {distance})
    """)

    pv_no_wd_count = (
        Parkeervak.objects
        .filter(bgt_wegdeel=None)
        .filter(soort="FISCAAL")
        .count())

    log.debug(
        "Fiscale Parkeervakken zonder WegDeel %s van %s",
        pv_no_wd_count,
        Parkeervak.objects.count())


# @LogWith(log)
# def add_wegdeel_to_scans(distance=0.000001):
#    """
#    Each scan spot should have a wegdeel if it does not have a parkeervlak
#    """
#    log.debug('Add roadpart to each parking spot')
#
#    scans_no_road_count = ScanRaw.objects.count
#
#    log.debug(
#        "Before: Scans zonder WegDeel %s Scans %s",
#        scans_no_road_count(),
#        Scan.objects.count())
#
#    with connection.cursor() as c:
#        c.execute(f"""
#    WITH matched_scans AS (
#    DELETE FROM scans_scanraw s
#    USING wegdelen_wegdeel wd
#    WHERE ST_DWithin(s.geometrie, wd.geometrie, {distance})
#    ORDER BY s.scan_id,
#    LIMIT 100000
#    RETURNING
#        s.scan_id,
#        s.scan_moment,
#        s.device_id,
#        s.scan_source,
#        s.longitude,
#        s.latitude,
#        s.buurtcode,
#        s.afstand,
#        s.sperscode,
#        s.qualcode,
#        s.ff_df,
#        s.nha_nr,
#        s.nha_hoogte,
#        s.uitval_nachtrun,
#
#        wd.id,
#        wd.bgt_functie
#    )
#    INSERT INTO scans_scan(
#        scan_id,
#        scan_moment,
#        device_id,
#        scan_source,
#        longitude,
#        latitude,
#        buurtcode,
#        afstand,
#        sperscode,
#        qualcode,
#        ff_df,
#        nha_nr,
#        nha_hoogte,
#        uitval_nachtrun,
#
#        bgt_wegdeel,
#        bgt_wegdeel_functie
#        )
#    SELECT * FROM matched_scans;
#    """)
#
#    log.debug(
#        "After: Scans zonder WegDeel: %s Scans %s",
#        scans_no_road_count(),
#        Scan.objects.count())


# def copy_leftover():
#    """
#    Copy scans leftover also into the final dataset
#    """
#
#    log.debug(
#        "Scans without roadpart or parkspot %s",
#        ScanRaw.objects.count())
#
#    with connection.cursor() as c:
#        c.execute("""
#        INSERT INTO scans_scan(
#            scan_id,
#            scan_moment,
#            device_id,
#            scan_source,
#            longitude,
#            latitude,
#            buurtcode,
#            afstand,
#            sperscode,
#            qualcode,
#            ff_df,
#            nha_nr,
#            nha_hoogte,
#            uitval_nachtrun,
#            bgt_wegdeel_functie
#        )
#        SELECT
#            scan_id,
#            scan_moment,
#            device_id,
#            scan_source,
#            longitude,
#            latitude,
#            buurtcode,
#            afstand,
#            sperscode,
#            qualcode,
#            ff_df,
#            nha_nr,
#            nha_hoogte,
#            uitval_nachtrun,
#            'unknown' AS bgt_wegdeel_functie
#        FROM scans_scanraw;
#        """)
#
#    log.debug("Scans %s", Scan.objects.count())
#    log.debug("Scans Raw %s", ScanRaw.objects.count())
#

@LogWith(log)
def import_parkeervakken():
    log.debug('Import en Converteer parkeervakken naar WGS84')

    Parkeervak.objects.all().delete()

    with connection.cursor() as c:
        c.execute("""
    INSERT INTO wegdelen_parkeervak(
        id,
        straatnaam,
        soort,
        type,
        aantal,
        geometrie,
        point
        )
    SELECT
        parkeer_id,
        straatnaam,
        soort,
        type,
        aantal,
        ST_Transform(ST_SetSRID(geom, 28992), 4326),
        ST_Centroid(ST_Transform(ST_SetSRID(geom, 28992), 4326))
    FROM bv.parkeervakken pv
    """)

    log.debug("Alle    Vakken %s", Parkeervak.objects.all().count())
    log.debug("Fiscale Vakken %s",
              Parkeervak.objects.filter(soort='FISCAAL').count())


def import_bgt_wegdelen_from(bron, functie):
    """
    Importeerd data uit verschillende bronnen
    """
    with connection.cursor() as c:
        c.execute(f"""
    INSERT INTO wegdelen_wegdeel(
        id,
        bgt_functie,
        geometrie
    )
    SELECT
        identificatie_lokaalid,
        wd."{functie}",
        ST_CurveToLine(ST_Transform(ST_SetSRID(geometrie, 28992), 4326))
    FROM bgt."{bron}" wd
    """)

    log.debug("Wegdelen %s %s", WegDeel.objects.all().count(), bron)


@LogWith(log)
def import_wegdelen():
    log.debug('Importeer en Converteer wegdelen naar WGS84 Polygonen')

    WegDeel.objects.all().delete()

    bronnen = [
        ('BGT_OWGL_verkeerseiland', 'bgt_functie'),
        ('BGT_OWGL_berm', 'bgt_fysiekvoorkomen'),
        ('BGT_OTRN_open_verharding', 'bgt_fysiekvoorkomen'),
        ('BGT_OTRN_transitie', 'bgt_fysiekvoorkomen'),
        ('BGT_WGL_fietspad', 'bgt_functie'),
        ('BGT_WGL_voetgangersgebied', 'bgt_functie'),
        ('BGT_WGL_voetpad', 'bgt_functie'),
        ('BGT_WGL_parkeervlak', 'bgt_functie'),
        ('BGT_WGL_rijbaan_lokale_weg', 'bgt_functie'),
        ('BGT_WGL_rijbaan_regionale_weg', 'bgt_functie'),
    ]
    for bron, functie in bronnen:
        import_bgt_wegdelen_from(bron, functie)


@LogWith(log)
def import_buurten():
    """
    Build buurt dataset where we can add parkeervak information
    """
    Buurt.objects.all().delete()

    log.debug('Create buurten dataset < 1 min')
    with connection.cursor() as c:
        c.execute("""
    INSERT INTO wegdelen_buurt(
        id,
        code,
        naam,
        geometrie
    )
    SELECT
        id,
        vollcode,
        naam,
        ST_Transform(geometrie, 4326)
    FROM bag_buurt
    """)


@LogWith(log)
def add_buurt_to_parkeervak():
    """
    Given parkeervakken find buurt of each pv
    """
    log.debug('Add buurtcode to each parkeervak < 1 min')

    with connection.cursor() as c:
        c.execute("""
    UPDATE  wegdelen_parkeervak pv
    SET buurt = b.code
    FROM wegdelen_buurt b
    WHERE ST_Contains(b.geometrie, pv.point)
    """)

    log.debug("Parkeeervak zonder buurt %s",
              Parkeervak.objects.filter(buurt=None).count())


@LogWith(log)
def add_parkeervak_count_to_wegdeel():
    """
    Each wegdeel needs to have a count of parkeervakken.
    """
    log.debug('Add parkeervak count to each wegdeel ~ 1 min')

    def status(state):

        log.debug(
            "%6s Wegdelen met parkeervak count %s",
            state,
            WegDeel.objects.filter(vakken__gt=0).count())

        log.debug(
            "%6s Wegdelen met fiscale pv count %s",
            state,
            WegDeel.objects.filter(fiscale_vakken__gt=0).count())

    status('before')

    with connection.cursor() as c:
        c.execute("""

    UPDATE wegdelen_wegdeel wd SET vakken=sq.vakken
    FROM (
        SELECT bgt_wegdeel, count(id) as vakken
        FROM wegdelen_parkeervak
            GROUP BY bgt_wegdeel
        )
        AS sq
        WHERE wd.id = bgt_wegdeel
    """)

    with connection.cursor() as c:
        c.execute("""
    UPDATE wegdelen_wegdeel wd SET fiscale_vakken=sq.vakken
    FROM (
        SELECT bgt_wegdeel, count(id) as vakken
        FROM wegdelen_parkeervak
        WHERE soort = 'FISCAAL'
            GROUP BY bgt_wegdeel
        )
        AS sq
        WHERE wd.id = bgt_wegdeel
    """)

    status('after')


@LogWith(log)
def add_parkeervak_count_to_buurt():
    """
    Each buurt needs to have count of parkeervakken
    """
    log.debug('Add parkeervak count to each buurt < (1 min)')

    def status(state):
        log.debug(
            "%6s: Buurt zonder pv count %s",
            state,
            WegDeel.objects.filter(vakken=None).count())

    status('before')

    with connection.cursor() as c:
        c.execute("""
    UPDATE wegdelen_buurt b SET vakken=sq.vakken
    FROM (
        SELECT buurt, count(id) as vakken
        FROM wegdelen_parkeervak
            GROUP BY buurt
        )
        AS sq
        WHERE id = buurt
    """)

    status('after')