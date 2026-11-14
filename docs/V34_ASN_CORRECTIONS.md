# v34 corporate ASN correction

The company allowlist falls from 55 to 54 unique origins. The correction removes 13 incorrect or retired mappings and adds 12 verified first-party origins. It does not deny those networks if they qualify independently by the unchanged RU RIR or GeoIP/RU policy.

| Previous override | Verified operator or status | Corrected company origins |
|---|---|---|
| Kaspersky [AS35598](https://bgp.he.net/AS35598) | INETCOM CARRIER LLC | AS209030 (already present) |
| Kaspersky [AS199945](https://bgp.he.net/AS199945) | BILLING SOLUTION Ltd. | AS209030 (already present) |
| Avito [AS49368](https://bgp.he.net/AS49368) | DomoLAN Ltd. | AS201012 |
| 2GIS [AS50952](https://bgp.he.net/AS50952) | Global Network Management Inc / DataIX route server | AS197482 |
| Kontur [AS41668](https://bgp.he.net/AS41668) | ER-Telecom Holding | AS49675 |
| 1C [AS48642](https://bgp.he.net/AS48642) | JSC For | No replacement without independent evidence |
| Positive Technologies [AS48061](https://bgp.he.net/AS48061) | GPM Digital Technologies LLC | No replacement without independent evidence |
| RUTUBE [AS48190](https://bgp.he.net/AS48190) | T2 Mobile LLC | AS207353 |
| T-Bank [AS200676](https://bgp.he.net/AS200676) | Svens Jansons | AS43399, AS205638, AS12686 |
| Alfa-Bank [AS30854](https://bgp.he.net/AS30854) | Velnet Telecom LLC | AS15632, AS59840 |
| VTB [AS25476](https://rirtracker.com/ripe/reports/2014-08-18/) | Deregistered and not in the observed ipverse archive | AS41551 |
| Gazprombank [AS30972](https://bgp.he.net/AS30972) | Bedrock SAS | AS35022 |
| Raiffeisenbank-RU [AS29194](https://bgp.he.net/AS29194) | MTS PJSC | AS31174 |

Evidence for the replacement origins is linked in the [allowlist](../geoip_RU_company_asns.txt). RUTUBE identifies Ruform as its operator in its [user agreement](https://rutube.ru/info/agreement/). [RIPE WHOIS for AS197482](https://bgp.he.net/AS197482) identifies the former AS50952 entry as a DataIX route server peer, not a DoubleGIS origin.

The origin selector still reads the committed registry first, and a matching embedded copy is used when that file is missing. Its self-test checks the corrected required origins and prevents reintroduction of the removed mappings. Unverified substitutes for 1C and Positive Technologies were not added. Kaspersky keeps its already verified Russian origin AS209030.

## Fixed-input regression replay

The unmodified workflow reproduced the published original DAT byte for byte (SHA-256 `778acd9da7b13b18c4942b626f09f809d3a23fd05d4d29bb404439a7eb0b5152`). Rebuilding with the same upstream and registry inputs changed only the company-origin registry and its validation.

- RU IPv4: 49,530,207 → 49,525,599. Exactly 4,608 removed across seven CIDRs, zero added. Bedrock SAS accounts for 4,096 and the old DataIX entry for 512.
- RU IPv6: nine CIDRs removed, zero added. Old origins were Bedrock SAS (two), DataIX (two) and AS200676 (five).
- PRIVATE coverage was identical. 2GIS, Gazprombank and the other newly listed genuine Russian origins already had coverage through the independent RIR/BGP path on this snapshot.
- Corrected test DAT SHA-256: `82edca0cb995bba62db3b1383fe168d70d27bdb00a0e8f4e807c7c994061e7a1`. Daily builds can differ as upstream sources rotate.

- Go builder tests, workflow validation and sing-box checks passed. The compiled RU and PRIVATE SRS files were decompiled and matched the DAT.
