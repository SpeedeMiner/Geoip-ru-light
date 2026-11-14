#!/usr/bin/env python3
"""Export and round-trip verify sing-box rule-sets from this project's GeoIP DAT."""

import argparse
import hashlib
import ipaddress
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory


CATEGORIES = ("RU", "PRIVATE")
RULE_SET_VERSION = 1


def read_varint(data, offset):
    value = 0
    for shift in range(0, 64, 7):
        if offset >= len(data):
            break
        byte = data[offset]
        offset += 1
        if shift == 63 and byte > 1:
            break
        value |= (byte & 0x7F) << shift
        if byte < 128:
            return value, offset
    raise ValueError("Invalid GeoIP protobuf varint")


def protobuf_fields(data, schema):
    """Decode the scalar and message fields emitted by the Light DAT writer."""
    offset = 0
    while offset < len(data):
        tag, offset = read_varint(data, offset)
        field, wire_type = tag >> 3, tag & 7
        if field not in schema or schema[field] != wire_type:
            raise ValueError(f"Unexpected GeoIP protobuf field {field}/{wire_type}")
        value, offset = read_varint(data, offset)
        if wire_type == 2:
            end = offset + value
            if end > len(data):
                raise ValueError("Truncated GeoIP protobuf field")
            value, offset = data[offset:end], end
        yield field, value


def parse_cidr(data):
    fields = list(protobuf_fields(data, {1: 2, 2: 0}))
    values = dict(fields)
    if len(values) != len(fields) or 1 not in values:
        raise ValueError("Invalid CIDR record in GeoIP DAT")
    # Proto3 omits the prefix field for /0.
    return ipaddress.ip_network((ipaddress.ip_address(values[1]), values.get(2, 0)))


def coverage(networks):
    """Canonical address coverage, computed separately for IPv4 and IPv6."""
    families = {4: [], 6: []}
    for network in networks:
        families[network.version].append(network)
    return [
        str(network)
        for family in (4, 6)
        for network in ipaddress.collapse_addresses(families[family])
    ]


def parse_geoip_dat(path):
    # GeoIPList, GeoIP, CIDR from v2ray-core's app/router/routercommon/common.proto.
    categories = {}
    for _, entry in protobuf_fields(path.read_bytes(), {1: 2}):
        name = None
        prefixes = []
        for field, value in protobuf_fields(entry, {1: 2, 2: 2, 3: 0}):
            if field == 1:
                if name is not None:
                    raise ValueError("Repeated category name in GeoIP DAT")
                name = value.decode("ascii")
            elif field == 2:
                prefixes.append(parse_cidr(value))
            elif value:
                raise ValueError("Inverse GeoIP categories are not supported")
        if name not in CATEGORIES or name in categories or not prefixes:
            raise ValueError(f"Unexpected, duplicate or empty GeoIP category: {name!r}")
        categories[name] = coverage(prefixes)
    if set(categories) != set(CATEGORIES):
        raise ValueError(f"Expected RU and PRIVATE in {path}, got {sorted(categories)}")
    return categories


def compile_and_verify(sing_box, work, category, expected):
    name = f"geoip_{category}.srs"
    source = work / f"{category}.json"
    binary = work / name
    decompiled = work / f"{category}.decompiled.json"
    source.write_text(
        json.dumps({"version": RULE_SET_VERSION, "rules": [{"ip_cidr": expected}]},
                   separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    subprocess.run([sing_box, "rule-set", "compile", "--output", str(binary), str(source)],
                   check=True)
    if not binary.is_file() or not binary.stat().st_size:
        raise ValueError(f"Missing or empty compiled rule-set: {name}")

    subprocess.run([sing_box, "rule-set", "decompile", "--output", str(decompiled), str(binary)],
                   check=True)
    result = json.loads(decompiled.read_text(encoding="utf-8"))
    rules = result.get("rules", [])
    if (result.get("version") != RULE_SET_VERSION or len(rules) != 1
            or set(rules[0]) != {"ip_cidr"} or not isinstance(rules[0]["ip_cidr"], list)):
        raise ValueError(f"Unexpected decompiled rule-set structure: {name}")
    actual = coverage(ipaddress.ip_network(cidr) for cidr in rules[0]["ip_cidr"])
    if actual != expected:
        missing = sorted(set(expected) - set(actual))[:3]
        added = sorted(set(actual) - set(expected))[:3]
        raise ValueError(f"{name} coverage mismatch: expected-only {missing}, actual-only {added}")
    print(f"{name}: verified {len(expected)} canonical CIDRs "
          f"({sum(':' not in cidr for cidr in expected)} IPv4, "
          f"{sum(':' in cidr for cidr in expected)} IPv6)")
    return binary


def build(geoip, output_dir, sing_box):
    categories = parse_geoip_dat(geoip)
    output_dir.mkdir(parents=True, exist_ok=True)
    # Stage both rule-sets and checksum files before exposing any output.
    with TemporaryDirectory(prefix=".geoip-srs-", dir=output_dir) as tmp:
        work = Path(tmp)
        outputs = []
        for category in CATEGORIES:
            binary = compile_and_verify(sing_box, work, category, categories[category])
            checksum = work / f"{binary.name}.sha256sum"
            checksum.write_text(f"{hashlib.sha256(binary.read_bytes()).hexdigest()}  {binary.name}\n",
                                encoding="ascii")
            outputs.extend((binary, checksum))
        for output in outputs:
            output.replace(output_dir / output.name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geoip", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("."))
    parser.add_argument("--sing-box", default="sing-box")
    args = parser.parse_args()
    build(args.geoip, args.output_dir, args.sing_box)


if __name__ == "__main__":
    main()
