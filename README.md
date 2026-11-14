# Geoip-ru-light

Клиентская база GeoIP RU/DIRECT. Для Xray/V2Ray используйте
`geoip_RU.dat` с категориями `geoip:RU` и `geoip:PRIVATE`.

## sing-box

| Набор | Что содержит | Скачать | SHA-256 |
| --- | --- | --- | --- |
| `geoip_RU.srs` | Категория `RU` из DAT, включая сети политики DIRECT | [SRS](https://raw.githubusercontent.com/SpeedeMiner/Geoip-ru-light/release/geoip_RU.srs) | [SHA-256](https://raw.githubusercontent.com/SpeedeMiner/Geoip-ru-light/release/geoip_RU.srs.sha256sum) |
| `geoip_PRIVATE.srs` | Категория `PRIVATE` из DAT, локальные и специальные сети | [SRS](https://raw.githubusercontent.com/SpeedeMiner/Geoip-ru-light/release/geoip_PRIVATE.srs) | [SHA-256](https://raw.githubusercontent.com/SpeedeMiner/Geoip-ru-light/release/geoip_PRIVATE.srs.sha256sum) |

Оба набора также публикуются в [релизе v34](https://github.com/SpeedeMiner/Geoip-ru-light/releases/tag/latest-geoip-client-v34).
Они содержат те же адреса IPv4 и IPv6, что и соответствующие категории в
`geoip_RU.dat` из той же сборки. Бинарный формат rule-set v1 поддерживается
начиная с sing-box 1.8.0.

Добавьте в `route.rule_set` нужные элементы:

```json
[
  {
    "type": "remote",
    "tag": "geoip-ru",
    "format": "binary",
    "url": "https://raw.githubusercontent.com/SpeedeMiner/Geoip-ru-light/release/geoip_RU.srs"
  },
  {
    "type": "remote",
    "tag": "geoip-private",
    "format": "binary",
    "url": "https://raw.githubusercontent.com/SpeedeMiner/Geoip-ru-light/release/geoip_PRIVATE.srs"
  }
]
```

Укажите соответствующие теги в `route.rules[].rule_set`. Сами наборы
содержат только IP-условия и не выбирают outbound.

### Локальная сборка

Имея готовый `geoip_RU.dat`, Python 3 и sing-box с командами
`rule-set compile` и `rule-set decompile` (в CI используется 1.13.12):

```sh
python3 scripts/build_sing_box_srs.py --geoip geoip_RU.dat
sha256sum -c geoip_RU.srs.sha256sum geoip_PRIVATE.srs.sha256sum
```
