import ipaddress
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from build_sing_box_srs import build, coverage, parse_geoip_dat


def varint(value):
    output = bytearray()
    while value >= 128:
        output.append((value & 127) | 128)
        value >>= 7
    return bytes(output) + bytes([value])


def message_field(field, data):
    return varint(field * 8 + 2) + varint(len(data)) + data


def entry(name, cidrs, inverse=False):
    result = message_field(1, name.encode("ascii"))
    for cidr in cidrs:
        network = ipaddress.ip_network(cidr)
        record = message_field(1, network.network_address.packed)
        if network.prefixlen:
            record += b"\x10" + varint(network.prefixlen)
        result += message_field(2, record)
    if inverse:
        result += b"\x18\x01"
    return message_field(1, result)


class ExportTest(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.geoip = self.root / "fixture.dat"
        self.ru = entry("RU", ["203.0.113.128/25", "2001:db8::/32", "203.0.113.0/25"])
        self.private = entry("PRIVATE", ["fc00::/7", "10.0.0.0/8"])

    def test_parse_and_collapse_both_families(self):
        self.geoip.write_bytes(self.private + self.ru)
        self.assertEqual(parse_geoip_dat(self.geoip), {
            "RU": ["203.0.113.0/24", "2001:db8::/32"],
            "PRIVATE": ["10.0.0.0/8", "fc00::/7"],
        })

    def test_proto3_omits_zero_prefix(self):
        self.geoip.write_bytes(entry("RU", ["0.0.0.0/0", "::/0"]) + self.private)
        self.assertEqual(parse_geoip_dat(self.geoip)["RU"], ["0.0.0.0/0", "::/0"])

    def test_reject_bad_geoip(self):
        bad_inputs = {
            "truncated": self.ru + self.private[:-1],
            "invalid varint": b"\x80" * 11,
            "unexpected category": self.private + entry("ZZ", ["192.0.2.0/24"]),
            "duplicate category": self.ru + self.private + self.ru,
            "missing category": self.ru,
            "empty category": self.ru + entry("PRIVATE", []),
            "inverse category": self.ru + entry("PRIVATE", ["10.0.0.0/8"], inverse=True),
        }
        for name, data in bad_inputs.items():
            with self.subTest(name=name):
                self.geoip.write_bytes(data)
                with self.assertRaises(ValueError):
                    parse_geoip_dat(self.geoip)

    def test_equivalent_split_and_reordered_coverage(self):
        original = ["203.0.113.0/24", "2001:db8::/32"]
        split = ["2001:db8::/32", "203.0.113.128/25", "203.0.113.0/25"]
        self.assertEqual(coverage(map(ipaddress.ip_network, original)),
                         coverage(map(ipaddress.ip_network, split)))

    def test_wrong_private_coverage_does_not_publish_ru(self):
        self.geoip.write_bytes(self.ru + self.private)
        output = self.root / "out"

        def fake_sing_box(cmd, check):
            target = Path(cmd[-2])
            if cmd[2] == "compile":
                target.write_text(Path(cmd[-1]).read_text())
            else:
                document = json.loads(Path(cmd[-1]).read_text())
                if Path(cmd[-1]).stem == "geoip_PRIVATE":
                    # Same CIDR count and sizes, but the IPv4 range has moved.
                    document["rules"][0]["ip_cidr"][0] = "11.0.0.0/8"
                target.write_text(json.dumps(document))

        with patch("build_sing_box_srs.subprocess.run", side_effect=fake_sing_box):
            with self.assertRaisesRegex(ValueError, "geoip_PRIVATE.srs coverage mismatch"):
                build(self.geoip, output, "sing-box")
        self.assertEqual(list(output.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
