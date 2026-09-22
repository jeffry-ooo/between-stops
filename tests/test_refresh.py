import copy
import datetime as dt
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from refresh_data import refresh, validate_bundle, validate_feed
from build_routes import service_calendar


class RefreshSafetyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.feed = self.root / 'feed.zip'
        self.today = dt.date(2026, 9, 22)
        self.tables = {
            'feed_info.txt': 'feed_start_date,feed_end_date\n20260901,20261031\n',
            'routes.txt': 'route_id,route_type\nbus,3\nmetro,1\n',
            'stops.txt': 'stop_id,stop_lat,stop_lon\na,41.38,2.16\nb,41.39,2.17\nx,41.40,2.18\n',
            'trips.txt': 'trip_id,route_id,service_id\nt,bus,s\n',
            'stop_times.txt': 'trip_id,stop_id,stop_sequence\nt,a,1\nt,b,2\n',
            'calendar.txt': 'service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date\ns,1,1,1,1,1,1,1,20260901,20261031\n',
            'calendar_dates.txt': 'service_id,date,exception_type\ns,20260922,2\n',
        }
        self.write_feed()
        self.bundle = {'city': {'slug': 'barcelona'}, 'all_pois': [{'name': 'Sight'}],
            'loops': [{'line': '59', 'route_id': 'bus', 'trip_id': 't',
                'shape': [[41.38, 2.16], [41.39, 2.17]],
                'stops': [{'stop_id': s, 'lat': 41.38, 'lon': 2.16,
                           'pois': [{'name': 'Sight'}]} for s in ['a', 'b']]}]}

    def write_feed(self):
        with zipfile.ZipFile(self.feed, 'w') as z:
            for name, value in self.tables.items():
                z.writestr(name, value)

    def test_valid_feed_and_bus_bundle(self):
        active = validate_feed(self.feed, self.today)
        self.assertEqual(active['s'], 6)  # calendar exception is respected
        validate_bundle(self.bundle, self.bundle, self.feed, active)

    def test_expired_future_and_near_expiry_feeds_rejected(self):
        for start, end in [('20260101', '20260201'), ('20261001', '20261031'), ('20260901', '20260923')]:
            with self.subTest(end=end):
                self.tables['feed_info.txt'] = f'feed_start_date,feed_end_date\n{start},{end}\n'
                self.write_feed()
                with self.assertRaises(ValueError):
                    validate_feed(self.feed, self.today)

    def test_empty_table_and_corrupt_download_rejected(self):
        self.tables['stops.txt'] = 'stop_id,stop_lat,stop_lon\n'
        self.write_feed()
        with self.assertRaises(ValueError):
            validate_feed(self.feed, self.today)
        self.feed.write_text('<html>upstream failure</html>')
        with self.assertRaises(zipfile.BadZipFile):
            validate_feed(self.feed, self.today)

    def test_non_bus_inactive_trip_wrong_stop_and_coverage_loss_rejected(self):
        for fault in ['rail', 'inactive', 'stop', 'coverage', 'coordinates', 'line']:
            with self.subTest(fault=fault):
                b = copy.deepcopy(self.bundle)
                active = {'s': 6}
                loop = b['loops'][0]
                if fault == 'rail': loop['route_id'] = 'metro'
                if fault == 'inactive': active = {'s': 0}
                if fault == 'stop': loop['stops'][0]['stop_id'] = 'x'
                if fault == 'coverage':
                    for st in loop['stops']: st['pois'] = []
                if fault == 'coordinates': loop['shape'][0][0] = float('nan')
                if fault == 'line': loop['line'] = '99'
                with self.assertRaises(ValueError):
                    validate_bundle(b, self.bundle, self.feed, active)

    def test_failure_preserves_published_bytes(self):
        (self.root / 'site').mkdir()
        (self.root / 'scripts').mkdir()
        target = self.root / 'site/routes.barcelona.json'
        original = json.dumps(self.bundle).encode()
        target.write_bytes(original)
        self.feed.write_text('broken ZIP')
        with self.assertRaises(zipfile.BadZipFile):
            refresh(self.root, self.feed)
        self.assertEqual(target.read_bytes(), original)
        self.write_feed()
        with patch('refresh_data.validate_feed', return_value={'s': 6}), \
             patch('refresh_data.subprocess.run', side_effect=RuntimeError('builder failed')):
            with self.assertRaises(RuntimeError):
                refresh(self.root, self.feed)
        self.assertEqual(target.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
