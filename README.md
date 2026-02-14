# Bambu Lab RFID Library

> [!NOTE]
> If you enjoy this project and want to help with its maintenance, please consider supporting me via Ko-Fi!
>
> <a href='https://ko-fi.com/queengooborg' target='_blank'><img height='36' style='border:0px;height:36px;' src='https://storage.ko-fi.com/cdn/kofi4.png?v=6' border='0' alt='Buy Me a Coffee at ko-fi.com' /></a>

This repository contains a collection of RFID tag scans from Bambu Lab filament spools. The data can be used to create cloned tags for Bambu Lab printers or for research purposes.

For more information about Bambu Lab RFID tags and their format, see https://github.com/queengooborg/Bambu-Lab-RFID-Tag-Guide.

## Viewing Tag Data

A script is included in this repository, `parse.py`, that will parse a tag dump and extract its information in an easy-to-read terminal output and easy-to-parse JSON format. To run it, simply run `python3 parse.py [/path/to/tag.bin-or-json]`.

## Contributing

The best way to contribute is to provide data for Bambu Lab RFID tags. Not sure how to obtain the data? Check out the [guide written in the Bambu Lab RFID Tag Guide repository](https://github.com/queengooborg/Bambu-Lab-RFID-Tag-Guide/blob/main/docs/ReadTags.md)!

Tags are stored in the following folder structure: `Material Category` > `Material Name` > `Color Name` > `Tag UID` > `Tag Files`

## List of Bambu Lab Materials + Colors

Status Icon Legend:

- ✅: Have tag data
- ❌: No tag scanned
- ⚠️: See notes
- ⏳: Tag data is for an older version of material

### PLA

#### PLA Basic

| Color                                                 | Filament Code | Variant ID | Status |
| ----------------------------------------------------- | ------------- | ---------- | ------ |
| [Jade White](PLA/PLA%20Basic/Jade%20White)            | 10100         | A00-W1     | ✅     |
| [Beige](PLA/PLA%20Basic/Beige)                        | 10201         | A00-P0     | ✅     |
| [Light Gray](PLA/PLA%20Basic/Light%20Gray)            | 10104         | A00-D2     | ✅     |
| [Yellow](PLA/PLA%20Basic/Yellow)                      | 10400         | A00-Y0     | ✅     |
| [Sunflower Yellow](PLA/PLA%20Basic/Sunflower%20Yellow)| 10402         | A00-Y2     | ✅     |
| [Pumpkin Orange](PLA/PLA%20Basic/Pumpkin%20Orange)    | 10301         | A00-A1     | ✅     |
| [Orange](PLA/PLA%20Basic/Orange)                      | 10300         | A00-A0     | ✅     |
| [Gold](PLA/PLA%20Basic/Gold)                          | 10401         | A00-Y4     | ✅     |
| [Bright Green](PLA/PLA%20Basic/Bright%20Green)        | 10503         | A00-G3     | ✅     |
| [Bambu Green](PLA/PLA%20Basic/Bambu%20Green)          | 10501         | A00-G1/G6  | ✅     |
| [Mistletoe Green](PLA/PLA%20Basic/Mistletoe%20Green)  | 10502         | A00-G2     | ✅     |
| [Pink](PLA/PLA%20Basic/Pink)                          | 10203         | A00-A0     | ✅     |
| [Hot Pink](PLA/PLA%20Basic/Hot%20Pink)                | 10204         | A00-R3     | ✅     |
| [Magenta](PLA/PLA%20Basic/Magenta)                    | 10202         | A00-P6     | ✅     |
| [Red](PLA/PLA%20Basic/Red)                            | 10200         | A00-R0     | ✅     |
| [Maroon Red](PLA/PLA%20Basic/Maroon%20Red)            | 10205         | A00-R2     | ✅     |
| [Purple](PLA/PLA%20Basic/Purple)                      | 10700         | A00-P5     | ✅     |
| [Indigo Purple](PLA/PLA%20Basic/Indigo%20Purple)      | 10701         | A00-P2     | ✅     |
| [Turquoise](PLA/PLA%20Basic/Turquoise)                | 10605         | A00-B5     | ✅     |
| [Cyan](PLA/PLA%20Basic/Cyan)                          | 10603         | A00-B8     | ✅     |
| [Cobalt Blue](PLA/PLA%20Basic/Cobalt%20Blue)          | 10604         | A00-B3     | ✅     |
| [Blue](PLA/PLA%20Basic/Blue)                          | 10601         | A09-B4     | ✅     |
| [Brown](PLA/PLA%20Basic/Brown)                        | 10800         | A00-N0     | ✅     |
| [Cocoa Brown](PLA/PLA%20Basic/Cocoa%brown)            | 10802         | A00-N1     | ✅     |
| [Bronze](PLA/PLA%20Basic/Bronze)                      | 10801         | A00-Y3     | ✅     |
| [Gray](PLA/PLA%20Basic/Gray)                          | 10103         | A00-D0     | ✅     |
| [Silver](PLA/PLA%20Basic/Silver)                      | 10102         | A00-D1     | ✅     |
| [Blue Grey](PLA/PLA%20Basic/Blue%20Grey)              | 10602         | A00-B1     | ✅     |
| [Dark Gray](PLA/PLA%20Basic/Dark%20Gray)              | 10105         | A00-D3     | ✅     |
| [Black](PLA/PLA%20Basic/Black)                        | 10101         | A00-K0     | ✅     |

#### PLA Lite

| Color                                       | Filament Code | Variant ID | Status |
| ------------------------------------------- | ------------- | ---------- | ------ |
| [Black](PLA/PLA%20Lite/Black)               | 16100         | A18-K0     | ✅     |
| [Gray](PLA/PLA%20Lite/Gray)                 | 16101         | A18-D0     | ✅     |
| [White](PLA/PLA%20Lite/White)               | 16103         | A18-W0     | ✅     |
| [Red](PLA/PLA%20Lite/Red)                   | 16200         | A18-R0     | ✅     |
| [Yellow](PLA/PLA%20Lite/Yellow)             | 16400         | A18-Y0     | ✅     |
| [Cyan](PLA/PLA%20Lite/Cyan)                 | 16600         | A18-B0     | ✅     |
| [Blue](PLA/PLA%20Lite/Blue)                 | 16601         | A18-B1     | ✅     |
| [Matte Beige](PLA/PLA%20Lite/Matte%20Beige) | 16602         | A18-P0     | ✅     |

#### PLA Matte

| Color                                                | Filament Code | Variant ID | Status |
| ---------------------------------------------------- | ------------- | ---------- | ------ |
| [Ivory White](PLA/PLA%20Matte/Ivory%20White)         | 11100         | A01-W2     | ✅     |
| [Bone White](PLA/PLA%20Matte/Bone%20White)           | 11103         | A01-W3     | ✅     |
| [Lemon Yellow](PLA/PLA%20Matte/Lemon%20Yellow)       | 11400         | A01-Y2     | ✅     |
| [Mandarin Orange](PLA/PLA%20Matte/Mandarin%20Orange) | 11300         | A01-A2     | ✅     |
| [Sakura Pink](PLA/PLA%20Matte/Sakura%20Pink)         | 11201         | A01-P3     | ✅     |
| [Lilac Purple](PLA/PLA%20Matte/Lilac%20Purple)       | 11700         | A01-P4     | ✅     |
| [Plum](PLA/PLA%20Matte/Plum)                         | 11204         | A01-R3     | ✅     |
| [Scarlet Red](PLA/PLA%20Matte/Scarlet%20Red)         | 11200         | A01-R1     | ✅     |
| [Dark Red](PLA/PLA%20Matte/Dark%20Red)               | 11202         | A01-R4     | ✅     |
| [Apple Green](PLA/PLA%20Matte/Apple%20Green)         | 11502         | A01-G0     | ✅     |
| [Grass Green](PLA/PLA%20Matte/Grass%20Green)         | 11500         | A01-G1     | ✅     |
| [Dark Green](PLA/PLA%20Matte/Dark%20Green)           | 11501         | A01-G7     | ✅     |
| [Ice Blue](PLA/PLA%20Matte/Ice%20Blue)               | 11601         | A01-B4     | ✅     |
| [Sky Blue](PLA/PLA%20Matte/Sky%20Blue)               | 11603         | A01-B0     | ✅     |
| [Marine Blue](PLA/PLA%20Matte/Marine%20Blue)         | 11600         | A01-B3     | ✅     |
| [Dark Blue](PLA/PLA%20Matte/Dark%20Blue)             | 11602         | A01-B6     | ✅     |
| [Desert Tan](PLA/PLA%20Matte/Desert%20Tan)           | 11401         | A01-Y3     | ✅     |
| [Latte Brown](PLA/PLA%20Matte/Latte%20Brown)         | 11800         | A01-N1     | ✅     |
| [Caramel](PLA/PLA%20Matte/Caramel)                   | 11803         | A01-N3     | ✅     |
| [Terracotta](PLA/PLA%20Matte/Terracotta)             | 11203         | A01-R2     | ✅     |
| [Dark Brown](PLA/PLA%20Matte/Dark%20Brown)           | 11801         | A01-N2     | ✅     |
| [Dark Chocolate](PLA/PLA%20Matte/Dark%20Chocolate)   | 11802         | A01-N0     | ✅     |
| [Ash Gray](PLA/PLA%20Matte/Ash%20Gray)               | 11102         | A01-D3     | ✅     |
| [Nardo Gray](PLA/PLA%20Matte/Nardo%20Gray)           | 11104         | A01-D0     | ✅     |
| [Charcoal](PLA/PLA%20Matte/Charcoal)                 | 11101         | A01-K1     | ✅     |

#### PLA Basic Gradient

| Color                                                                    | Filament Code | Variant ID | Status |
| ------------------------------------------------------------------------ | ------------- | ---------- | ------ |
| [Pink Citrus](PLA/PLA%20Basic%20Gradient/Pink%20Citrus)                  | 10903         | A00-M3     | ✅     |
| [Dusk Glare](PLA/PLA%20Basic%20Gradient/Dusk%20Glare)                    | 10906         | A00-M6     | ✅     |
| [Arctic Whisper](PLA/PLA%20Basic%20Gradient/Artic%20Whisper)             | 10900         | A00-M0     | ✅     |
| [Solar Breeze](PLA/PLA%20Basic%20Gradient/Solar%20Breeze)                | 10901         | A00-M1     | ✅     |
| [Blueberry Bubblegum](PLA/PLA%20Basic%20Gradient/Blueberry%20Bubblegum)  | 10905         | A00-M5     | ✅     |
| [Mint Lime](PLA/PLA%20Basic%20Gradient/Mint%20Lime)                      | 10904         | A00-M4     | ✅     |
| [Ocean to Meadow](PLA/PLA%20Basic%20Gradient/Ocean%20to%20Meadow)        | 10902         | A00-M2     | ✅     |
| [Cotton Candy Cloud](PLA/PLA%20Basic%20Gradient/Cotton%20Candy%20Cloud)  | 10907         | A00-M7     | ✅     |

#### PLA Glow

| Color                           | Filament Code | Variant ID | Status |
| ------------------------------- | ------------- | ---------- | ------ |
| [Green](PLA/PLA%20Glow/Green)   | 15500         | A12-G0     | ✅     |
| [Pink](PLA/PLA%20Glow/Pink)     | 15200         | A12-R0     | ✅     |
| [Orange](PLA/PLA%20Glow/Orange) | 15300         | A12-A0     | ✅     |
| [Yellow](PLA/PLA%20Glow/Yellow) | 15400         | A12-Y0     | ✅     |
| [Blue](PLA/PLA%20Glow/Blue)     | 15600         | A12-B0     | ✅     |

#### PLA Marble

| Color                                           | Filament Code | Variant ID | Status |
| ----------------------------------------------- | ------------- | ---------- | ------ |
| [Red Granite](PLA/PLA%20Marble/Red%20Granite)   | 13201         | A07-R5     | ✅     |
| [White Marble](PLA/PLA%20Marble/White%20Marble) | 13103         | A07-D4     | ✅     |

#### PLA Aero

| Color                         | Filament Code | Variant ID | Status |
| ----------------------------- | ------------- | ---------- | ------ |
| [White](PLA/PLA%20Aero/White) | 14102         | A11-W0     | ✅     |
| [Gray](PLA/PLA%20Aero/Gray)   | 14104         | ?          | ❌     |
| [Black](PLA/PLA%20Aero/Black) | 14103         | A11-K0     | ✅     |

#### PLA Sparkle

| Color                                                             | Filament Code | Variant ID | Status |
| ----------------------------------------------------------------- | ------------- | ---------- | ------ |
| [Alpine Green Sparkle](PLA/PLA%20Sparkle/Alpine%20Green%20Sparke) | 13501         | A08-G3     | ✅     |
| [Slate Gray Sparkle](PLA/PLA%20Sparkle/Slate%20Gray%20Sparke)     | 13102         | A08-D5     | ✅     |
| [Royal Purple Sparkle](PLA/PLA%20Sparkle/Royal%20Purlpe%20Sparke) | 13700         | A08-B7     | ✅     |
| [Crimson Red Sparkle](PLA/PLA%20Sparkle/Crimson%20red%20Sparke)   | 13200         | A08-R2     | ✅     |
| [Onyx Black Sparkle](PLA/PLA%20Sparkle/Onyx%20Black%20Sparke)     | 13101         | A08-K2     | ✅     |
| [Classic Gold Sparkle](PLA/PLA%20Sparkle/Classic%20Gold%20Sparke) | 13402         | A08-Y1     | ✅     |

#### PLA Metal

| Color                                                               | Filament Code | Variant ID | Status |
| ------------------------------------------------------------------- | ------------- | ---------- | ------ |
| [Cobalt Blue Metallic](PLA/PLA%20Metal/Cobalt%20Blue%20Metallic)    | 13600         | A02-B2     | ✅     |
| [Oxide Green Metallic](PLA/PLA%20Metal/Oxide%20Green%20Metallic)    | 13500         | A02-G2     | ✅     |
| [Iridium Gold Metallic](PLA/PLA%20Metal/Iridium%20Gold%20Metallic)  | 13400         | A02-Y1     | ✅     |
| [Copper Brown Metallic](PLA/PLA%20Metal/Copper%20Brown%20Metallic)  | 13800         | A02-N3     | ✅     |
| [Iron Gray Metallic](PLA/PLA%20Metal/Iron%20Gray%20Metallic)        | 13100         | A02-D2     | ✅     |

#### PLA Translucent

| Color                                                  | Filament Code | Variant ID | Status |
| ------------------------------------------------------ | ------------- | ---------- | ------ |
| [Teal](PLA/PLA%20Translucent/Teal)                     | 13612         | ?          | ❌     |
| [Blue](PLA/PLA%20Translucent/Blue)                     | 13611         | A17-B1     | ✅     |
| [Orange](PLA/PLA%20Translucent/Orange)                 | 13301         | A17-A0     | ✅     |
| [Purple](PLA/PLA%20Translucent/Purple)                 | 13710         | A17-P0     | ✅     |
| [Red](PLA/PLA%20Translucent/Red)                       | 13210         | A17-R0     | ✅     |
| [Light Jade](PLA/PLA%20Translucent/Light%20Jade)       | 13510         | A17-G0     | ✅     |
| [Mellow Yellow](PLA/PLA%20Translucent/Mellow%20Yellow) | 13410         | A17-Y0     | ✅     |
| [Cherry Pink](PLA/PLA%20Translucent/Cherry%20Pink)     | 13211         | A17-R1     | ✅     |
| [Ice Blue](PLA/PLA%20Translucent/Ice%Blue)             | 13610         | ?          | ❌     |
| [Lavender](PLA/PLA%20Translucent/Lavender)             | 13711         | A17-P1     | ✅     |

#### PLA Silk+

| Color                                        | Filament Code | Variant ID | Status |
| -------------------------------------------- | ------------- | ---------- | ------ |
| [Gold](PLA/PLA%20Silk+/Gold)                 | 13405         | A06-Y1     | ✅     |
| [Titan Gray](PLA/PLA%20Silk+/Titan%20Gray)   | 13108         | A06-D0     | ✅     |
| [Silver](PLA/PLA%20Silk+/Silver)             | 13109         | A06-D1     | ✅     |
| [White](PLA/PLA%20Silk+/White)               | 13110         | A06-W0     | ✅     |
| [Candy Red](PLA/PLA%20Silk+/Candy%20Red)     | 13205         | A06-R0     | ✅     |
| [Candy Green](PLA/PLA%20Silk+/Candy%20Green) | 13506         | A06-G0     | ✅     |
| [Mint](PLA/PLA%20Silk+/Mint)                 | 13507         | A06-G1     | ✅     |
| [Blue](PLA/PLA%20Silk+/Blue)                 | 13604         | A06-B1     | ✅     |
| [Baby Blue](PLA/PLA%20Silk+/Baby%20Blue)     | 13603         | A06-B0     | ✅     |
| [Purple](PLA/PLA%20Silk+/Purple)             | 13702         | A06-P0     | ✅     |
| [Rose Gold](PLA/PLA%20Silk+/Rose%20Gold)     | 13206         | A06-R1     | ✅     |
| [Pink](PLA/PLA%20Silk+/Pink)                 | 13207         | A06-R2     | ✅     |
| [Champagne](PLA/PLA%20Silk+/Champagne)       | 13404         | A06-Y0     | ✅     |

#### PLA Silk Multi-Color

| Color                                                            | Filament Code | Variant ID | Status |
| ---------------------------------------------------------------- | ------------- | ---------- | ------ |
| [Champagne](PLA/PLA%20Silk%20Multi-Color/Champagne)              | 13404         | A06-Y0     | ✅     |
| [Dawn Radiance](PLA/PLA%20Silk%20Multi-Color/Dawn%20Radiance)    | 13912         | A05-M8     | ✅     |
| [Aurora Purple](PLA/PLA%20Silk%20Multi-Color/Aurora%20Purple)    | 13909         | A05-M4     | ✅     |
| [South Beach](PLA/PLA%20Silk%20Multi-Color/South%20Beach)        | 13906         | A05-M1     | ✅     |
| [Phantom Blue](PLA/PLA%20Silk%20Multi-Color/Phantom%20Blue)      | 13916         | ?          | ❌     |
| [Mystic Magenta](PLA/PLA%20Silk%20Multi-Color/Mystic%20Magenta)  | 13913         | ?          | ❌     |
| [Neon City](PLA/PLA%20Silk%20Multi-Color/Neon%20City)            | 13903         | A05-T3     | ✅     |
| [Midnight Blaze](PLA/PLA%20Silk%20Multi-Color/Midnight%20Blaze)  | 13902         | A05-T2     | ✅     |
| [Gilded Rose](PLA/PLA%20Silk%20Multi-Color/Gilded%20Rose)        | 13901         | A05-T1     | ✅     |
| [Blue Hawaii](PLA/PLA%20Silk%20Multi-Color/Blue%20Hawaii)        | 13904         | A05-T4     | ✅     |
| [Velvet Eclipse](PLA/PLA%20Silk%20Multi-Color/Velvet%20Eclipse)  | 13905         | A05-T5     | ✅     |

#### PLA Galaxy

| Color                               | Filament Code | Variant ID | Status |
| ----------------------------------- | ------------- | ---------- | ------ |
| [Purple](PLA/PLA%20Galaxy/Purple)   | 13602         | A15-B0     | ✅     |
| [Green](PLA/PLA%20Galaxy/Green)     | 13503         | A15-G0     | ✅     |
| [Nebulae](PLA/PLA%20Galaxy/Nebulae) | 13504         | A15-G1     | ✅     |
| [Brown](PLA/PLA%20Galaxy/Brown)     | 13203         | A15-R0     | ✅     |

#### PLA Wood

| Color                                           | Filament Code | Variant ID | Status |
| ----------------------------------------------- | ------------- | ---------- | ------ |
| [Black Walnut](PLA/PLA%20Wood/Black%20Walnut)   | 13107         | A16-K0     | ✅     |
| [Rosewood](PLA/PLA%20Wood/Rosewood)             | 13204         | A16-R0     | ✅     |
| [Clay Brown](PLA/PLA%20Wood/Clay%20Brown)       | 13801         | A16-N0     | ✅     |
| [Classic Birch](PLA/PLA%20Wood/Classic%20Birch) | 13505         | A16-G0     | ✅     |
| [White Oak](PLA/PLA%20Wood/White%20Oak)         | 13106         | A16-W0     | ✅     |
| [Ochre Yellow](PLA/PLA%20Wood/Ochre%20Yellow)   | 13403         | A16-Y0     | ✅     |

#### PLA-CF

| Color                                     | Filament Code | Variant ID | Status |
| ----------------------------------------- | ------------- | ---------- | ------ |
| [Burgundy Red](PLA/PLA-CF/Burgundy%20Red) | 14200         | ?          | ❌     |
| [Matcha Green](PLA/PLA-CF/Matcha%20Green) | 14500         | ?          | ❌     |
| [Lava Gray](PLA/PLA-CF/Lava%20gray)       | 14101         | A50-D6     | ✅     |
| [Jeans Blue](PLA/PLA-CF/Jeans%20Blue)     | 14600         | ?          | ❌     |
| [Black](PLA/PLA-CF/Black)                 | 14100         | A50-K0     | ✅     |
| [Royal Blue](PLA/PLA-CF/Royal%20Blue)     | 14601         | A50-B6     | ❌     |
| [Iris Purple](PLA/PLA-CF/Iris%20Purple)   | 14700         | ?          | ❌     |

#### PLA Tough+

| Color                             | Filament Code | Variant ID | Status |
| --------------------------------- | ------------- | ---------- | ------ |
| [Black](PLA/PLA%20Tough+/Black)   | 12104         | A10-K0     | ✅     |
| [White](PLA/PLA%20Tough+/White)   | 12107         | A10-W0     | ✅     |
| [Yellow](PLA/PLA%20Tough+/Yellow) | 12401         | ?          | ❌     |
| [Orange](PLA/PLA%20Tough+/Orange) | 12301         | ?          | ❌     |
| [Gray](PLA/PLA%20Tough+/Gray)     | 12105         | A10-D0     | ✅     |
| [Silver](PLA/PLA%20Tough+/Silver) | 12106         | ?          | ❌     |
| [Cyan](PLA/PLA%20Tough+/Cyan)     | 12601         | ?          | ❌     |

#### PLA Tough

| Color                                             | Filament Code | Variant ID | Status |
| ------------------------------------------------- | ------------- | ---------- | ------ |
| [Lavender Blue](PLA/PLA%20Tough/Lavender%20Blue)  | 12005         | A09-B5     | ✅     |
| [Light Blue](PLA/PLA%20Tough/Light%20Blue)        | 12004         | A09-B4     | ✅     |
| [Orange](PLA/PLA%20Tough/Orange)                  | 12002         | A09-A0     | ✅     |
| [Silver](PLA/PLA%20Tough/Silver)                  | 12001         | A09-D1     | ✅     |
| [Vermilion Red](PLA/PLA%20Tough/Vermillion%20Red) | 12003         | A09-R3     | ✅     |
| [Yellow](PLA/PLA%20Tough/Yellow)                  | 12000         | A09-Y0     | ✅     |

### PETG

#### PETG HF

| Color                                         | Filament Code | Variant ID | Status |
| --------------------------------------------- | ------------- | ---------- | ------ |
| [Black](PETG/PETG%20HF/Black)                 | 33102         | G02-K0     | ✅     |
| [White](PETG/PETG%20HF/White)                 | 33100         | G02-W0     | ✅     |
| [Red](PETG/PETG%20HF/Red)                     | 33200         | G02-R0     | ✅     |
| [Gray](PETG/PETG%20HF/Gray)                   | 33101         | G02-D0     | ✅     |
| [Dark Gray](PETG/PETG%20HF/Dark%20Gray)       | 33103         | G02-D1     | ✅     |
| [Cream](PETG/PETG%20HF/Cream)                 | 33401         | G02-Y1     | ✅     |
| [Yellow](PETG/PETG%20HF/Yellow)               | 33400         | G02-Y0     | ✅     |
| [Orange](PETG/PETG%20HF/Orange)               | 33300         | G02-A0     | ✅     |
| [Peanut Brown](PETG/PETG%20HF/Peanut%20Brown) | 33801         | G02-N1     | ✅     |
| [Lime Green](PETG/PETG%20HF/Lime%20Green)     | 33501         | G02-G1     | ✅     |
| [Green](PETG/PETG%20HF/Green)                 | 33500         | G02-G0     | ✅     |
| [Forest Green](PETG/PETG%20HF/Forest%20Green) | 33502         | G02-G2     | ✅     |
| [Lake Blue](PETG/PETG%20HF/Lake%20Blue)       | 33601         | G02-B1     | ✅     |
| [Blue](PETG/PETG%20HF/Blue)                   | 33600         | G02-B0     | ✅     |

#### PETG Translucent

| Color                                                                     | Filament Code | Variant ID | Status |
| ------------------------------------------------------------------------- | ------------- | ---------- | ------ |
| [Translucent Teal](PETG/PETG%20Translucent/Translucent%20Teal)            | 32501         | G01-G1     | ✅     |
| [Translucent Light Blue](PETG/PETG%20Translucent/Translucent%Light%20Blue) | 32600         | G01-B0     | ✅     |
| [Clear](PETG/PETG%20Translucent/Clear)                                     | 32101         | G01-C0     | ✅     |
| [Translucent Gray](PETG/PETG%20Translucent/Translucent%Gray)               | 32100         | G01-D0     | ✅     |
| [Translucent Olive](PETG/PETG%20Translucent/Translucent%Olive)             | 32500         | G01-G0     | ✅     |
| [Translucent Brown](PETG/PETG%20Translucent/Translucent%Brown)             | 32800         | G01-N0     | ✅     |
| [Translucent Orange](PETG/PETG%20Translucent/Translucent%Orange)           | 32300         | G01-A0     | ✅     |
| [Translucent Pink](PETG/PETG%20Translucent/Translucent%Pink)               | 32200         | G01-P1     | ✅     |
| [Translucent Purple](PETG/PETG%20Translucent/Translucent%Purple)           | 32700         | G01-P0     | ✅     |

#### PETG-CF

| Color                                               | Filament Code | Variant ID | Status |
| --------------------------------------------------- | ------------- | ---------- | ------ |
| [Indigo Blue](PETG/PETG%20CF/Indigo%20Blue)         | 31600         | ?          | ❌     |
| [Malachite Green](PETG/PETG%20CF/Malachite%20Green) | 31500         | G50-G7     | ✅     |
| [Titan Gray](PETG/PETG%20CF/Titan%20Gray)           | 31101         | G50-D6     | ✅     |
| [Brick Red](PETG/PETG%20CF/Brick%20Red)             | 31200         | ?          | ❌     |
| [Violet Purple](PETG/PETG%20CF/Violet%20Purple)     | 31700         | G50-P7     | ✅     |
| [Black](PETG/PETG%20CF/Black)                       | 31100         | G50-K0     | ✅     |

### ABS

#### ABS

| Color                                          | Filament Code | Variant ID | Status |
| ---------------------------------------------- | ------------- | ---------- | ------ |
| [Silver](ABS/ABS/Silver)                       | 40102         | B00-D1     | ✅     |
| [Black](ABS/ABS/Black)                         | 40101         | B00-K0     | ✅     |
| [White](ABS/ABS/White)                         | 40100         | B00-W0     | ✅     |
| [Bambu Green](ABS/ABS/Bambu%20Green)           | 40500         | B00-G6     | ✅     |
| [Olive](ABS/ABS/Olive)                         | 40502         | B00-G7     | ✅     |
| [Tangerine Yellow](ABS/ABS/Tangerine%20Yellow) | 40402         | B00-Y1     | ✅     |
| [Orange](ABS/ABS/Orange)                       | 40300         | B00-A0     | ✅     |
| [Red](ABS/ABS/Red)                             | 40200         | B00-R0     | ✅     |
| [Azure](ABS/ABS/Azure)                         | 40601         | B00-B4     | ✅     |
| [Blue](ABS/ABS/Blue)                           | 40600         | B00-B0     | ✅     |
| [Navy Blue](ABS/ABS/Navy%20Blue)               | 40602         | B00-B6     | ✅     |

#### ABS-GF

| Color                       | Filament Code | Variant ID | Status |
| --------------------------- | ------------- | ---------- | ------ |
| [Orange](ABS/ABS-GF/Orange) | 41300         | B50-A0     | ✅     |
| [Green](ABS/ABS-GF/Green)   | 41500         | B50-G0     | ❌     |
| [Red](ABS/ABS-GF/Red)       | 41200         | B50-R0     | ❌     |
| [Yellow](ABS/ABS-GF/Yellow) | 41400         | ?          | ❌     |
| [Blue](ABS/ABS-GF/Blue)     | 41600         | ?          | ❌     |
| [White](ABS/ABS-GF/White)   | 41100         | B50-W0     | ❌     |
| [Gray](ABS/ABS-GF/Gray)     | 41102         | ?          | ❌     |
| [Black](ABS/ABS-GF/Black)   | 41101         | B50-K0     | ✅     |

### ASA

#### ASA

| Color                  | Filament Code | Variant ID | Status |
| ---------------------- | ------------- | ---------- | ------ |
| [White](ASA/ASA/White) | 45100         | B01-W0     | ✅     |
| [Green](ASA/ASA/Green) | 45500         | ?          | ❌     |
| [Black](ASA/ASA/Black) | 45101         | B01-K0     | ✅     |
| [Gray](ASA/ASA/Gray)   | 45102         | B01-D0     | ✅     |
| [Red](ASA/ASA/Red)     | 45200         | B01-R0     | ✅     |
| [Blue](ASA/ASA/Blue)   | 45600         | ?          | ❌     |

#### ASA Aero

| Color                         | Filament Code | Variant ID | Status |
| ----------------------------- | ------------- | ---------- | ------ |
| [White](ASA/ASA%20Aero/White) | 46100         | B02-W0     | ✅     |

#### ASA-CF

| Color                    | Filament Code | Variant ID | Status |
| ------------------------ | ------------- | ---------- | ------ |
| [Black](ASA/ASA-CF/Black | 46101         | B51-K0     | ✅     |

### PC

#### PC

| Color                              | Filament Code | Variant ID | Status |
| ---------------------------------- | ------------- | ---------- | ------ |
| [Transparent](PC/PC/Transparent)   | 60103         | C00-C1     | ✅     |
| [Clear Black](PC/PC/Clear%20Black) | 60102         | C00-C0     | ✅     |
| [Black](PC/PC/Black)               | 60101         | C00-K0     | ✅     |
| [White](PC/PC/White)               | 60100         | C00-W0     | ✅     |

#### PC FR

| Color                     | Filament Code | Variant ID | Status |
| ------------------------- | ------------- | ---------- | ------ |
| [Black](PC/PC%20FR/Black) | 63100         | C01-K0     | ✅     |
| [White](PC/PC%20FR/White) | 63101         | C01-W0     | ✅     |
| [Gray](PC/PC%20FR/Gray)   | 63102         | C01-D0     | ✅     |

### TPU

#### TPU for AMS

| Color                                          | Filament Code | Variant ID | Status |
| ---------------------------------------------- | ------------- | ---------- | ------ |
| [Blue](TPU/TPU%20for%20AMS/Blue)               | 53600         | U02-B0     | ✅     |
| [Red](TPU/TPU%20for%20AMS/Red)                 | 53200         | ?          | ❌     |
| [Yellow](TPU/TPU%20for%20AMS/Yellow)           | 53400         | ?          | ❌     |
| [Neon Green](TPU/TPU%20for%20AMS/Neon%20Green) | 53500         | ?          | ❌     |
| [White](TPU/TPU%20for%20AMS/White)             | 53100         | ?          | ❌     |
| [Gray](TPU/TPU%20for%20AMS/Gray)               | 53102         | U02-D0     | ✅     |
| [Black](TPU/TPU%20for%20AMS/Black)             | 53101         | U02-K0     | ✅     |

### PA

#### PAHT-CF

| Color                     | Filament Code | Variant ID | Status |
| ------------------------- | ------------- | ---------- | ------ |
| [Black](PA/PAHT-CF/Black) | 70100         | N04-K0     | ✅     |

#### PA6-GF

| Color                      | Filament Code | Variant ID | Status |
| -------------------------- | ------------- | ---------- | ------ |
| [Blue](PA/PA6-GF/Blue)     | 72600         | ?          | ❌     |
| [Orange](PA/PA6-GF/Orange) | 72200         | ?          | ❌     |
| [Yellow](PA/PA6-GF/Yellow) | 72400         | ?          | ❌     |
| [Lime](PA/PA6-GF/Lime)     | 72500         | ?          | ❌     |
| [Brown](PA/PA6-GF/Brown)   | 72800         | ?          | ❌     |
| [White](PA/PA6-GF/White)   | 72102         | ?          | ❌     |
| [Gray](PA/PA6-GF/Gray)     | 72103         | ?          | ❌     |
| [Black](PA/PA6-GF/Black)   | 72104         | N08-K0     | ✅     |

### Support Material

#### Support for PLA/PETG

| Color                                                        | Filament Code | Variant ID           | Status |
| ------------------------------------------------------------ | ------------- | -------------------- | ------ |
| [Nature](Support%20Material/Support%20for%20PLA-PETG/Nature) | 65102         | S02-W0 (Old: S00-W0) | ✅     |
| [Black](Support%20Material/Support%20for%20PLA-PETG/Black)   | 65103         | S05-C0               | ✅     |

#### Support for PLA (New Version)

| Color                                                                   | Filament Code | Variant ID | Status |
| ----------------------------------------------------------------------- | ------------- | ---------- | ------ |
| [White](Support%20Material/Support%20for%20PLA%20(New%20Version)/White) | 65104         | S02-W1     | ✅     |

#### Support for ABS

| Color                                                 | Filament Code | Variant ID | Status |
| ----------------------------------------------------- | ------------- | ---------- | ------ |
| [White](Support%20Material/Support%20for%20ABS/White) | 66100         | S06-W0     | ✅     |

#### Support for PA/PET

| Color                                                    | Filament Code | Variant ID | Status |
| -------------------------------------------------------- | ------------- | ---------- | ------ |
| [Green](Support%20Material/Support%20for%20PA-PET/Green) | 65500         | S03-G1     | ✅     |

#### PVA

| Color                                 | Filament Code | Variant ID | Status |
| ------------------------------------- | ------------- | ---------- | ------ |
| [Clear](Support%20Material/PVA/Clear) | 66400         | S04-Y0     | ✅     |

## History

When Bambu Lab released the AMS for their 3D printers, it featured an RFID reader which could read RFID tags embedded on their filament spools to automatically update details such as material type, color and amount of remaining filament. However, the RFID tags were read-protected by keys, signed with an RSA2048 signature and structured in a proprietary format, which meant that only Bambu Lab could create these particular RFID tags and they could only be used on Bambu Lab printers. This led to the start of the [Bambu Research Group and a project to reverse engineer the RFID tag format](https://github.com/queengooborg/Bambu-Lab-RFID-Tag-Guide) in order to develop an open standard for all filament manufacturers and printers.

Of course, to research the tag format, a lot of tag data was required. This led to a community effort to scan lots of tags and cross-reference the data with known details about each spool. Eventually, enough of the format was reverse engineered to be able to determine what an open standard would need. But, the tag scanning didn't stop there, as the community realized another benefit to the collection of tags: even though custom tags couldn't be created due to the signing of the data, the data could be _cloned_ onto new tags and used to tell Bambu Lab printers what material and color a spool was, just like Bambu Lab first-party spools.

Originally, the collection of scanned tags was kept private as the research group was not sure if Bambu Lab would react negatively to sniffing data transfers to obtain hidden keys. However, as time progressed and new methods were discovered to obtain tag data, the group slowly opened up the tag collection and made it easier to access, until eventually it became the consensus to create this repository.
