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

| Color            | Filament Code | Variant ID | Status |
| ---------------- | ------------- | ---------- | ------ |
| Jade White       | 10100         | A00-W1     | ✅     |
| Beige            | 10201         | A00-P0     | ✅     |
| Light Gray       | 10104         | A00-D2     | ✅     |
| Yellow           | 10400         | A00-Y0     | ✅     |
| Sunflower Yellow | 10402         | A00-Y2     | ✅     |
| Pumpkin Orange   | 10301         | A00-A1     | ✅     |
| Orange           | 10300         | A00-A0     | ✅     |
| Gold             | 10401         | A00-Y4     | ✅     |
| Bright Green     | 10503         | A00-G3     | ✅     |
| Bambu Green      | 10501         | A00-G1/G6  | ✅     |
| Mistletoe Green  | 10502         | A00-G2     | ✅     |
| Pink             | 10203         | A00-A0     | ✅     |
| Hot Pink         | 10204         | A00-R3     | ✅     |
| Magenta          | 10202         | A00-P6     | ✅     |
| Red              | 10200         | A00-R0     | ✅     |
| Maroon Red       | 10205         | A00-R2     | ✅     |
| Purple           | 10700         | A00-P5     | ✅     |
| Indigo Purple    | 10701         | A00-P2     | ✅     |
| Turquoise        | 10605         | A00-B5     | ✅     |
| Cyan             | 10603         | A00-B8     | ✅     |
| Cobalt Blue      | 10604         | A00-B3     | ✅     |
| Blue             | 10601         | A09-B4     | ✅     |
| Brown            | 10800         | A00-N0     | ✅     |
| Cocoa Brown      | 10802         | A00-N1     | ✅     |
| Bronze           | 10801         | A00-Y3     | ✅     |
| Gray             | 10103         | A00-D0     | ✅     |
| Silver           | 10102         | A00-D1     | ✅     |
| Blue Grey        | 10602         | A00-B1     | ✅     |
| Dark Gray        | 10105         | A00-D3     | ✅     |
| Black            | 10101         | A00-K0     | ✅     |

#### PLA Lite

| Color       | Filament Code | Variant ID | Status |
| ----------- | ------------- | ---------- | ------ |
| Black       | 16100         | A18-K0     | ✅     |
| Gray        | 16101         | A18-D0     | ✅     |
| White       | 16103         | A18-W0     | ✅     |
| Red         | 16200         | A18-R0     | ✅     |
| Yellow      | 16400         | A18-Y0     | ✅     |
| Cyan        | 16600         | A18-B0     | ✅     |
| Blue        | 16601         | A18-B1     | ✅     |
| Matte Beige | 16602         | A18-P0     | ✅     |

#### PLA Matte

| Color           | Filament Code | Variant ID | Status |
| --------------- | ------------- | ---------- | ------ |
| Ivory White     | 11100         | A01-W2     | ✅     |
| Bone White      | 11103         | A01-W3     | ✅     |
| Lemon Yellow    | 11400         | A01-Y2     | ✅     |
| Mandarin Orange | 11300         | A01-A2     | ✅     |
| Sakura Pink     | 11201         | A01-P3     | ✅     |
| Lilac Purple    | 11700         | A01-P4     | ✅     |
| Plum            | 11204         | A01-R3     | ✅     |
| Scarlet Red     | 11200         | A01-R1     | ✅     |
| Dark Red        | 11202         | A01-R4     | ✅     |
| Apple Green     | 11502         | A01-G0     | ✅     |
| Grass Green     | 11500         | A01-G1     | ✅     |
| Dark Green      | 11501         | A01-G7     | ✅     |
| Ice Blue        | 11601         | A01-B4     | ✅     |
| Sky Blue        | 11603         | A01-B0     | ✅     |
| Marine Blue     | 11600         | A01-B3     | ✅     |
| Dark Blue       | 11602         | A01-B6     | ✅     |
| Desert Tan      | 11401         | A01-Y3     | ✅     |
| Latte Brown     | 11800         | A01-N1     | ✅     |
| Caramel         | 11803         | A01-N3     | ✅     |
| Terracotta      | 11203         | A01-R2     | ✅     |
| Dark Brown      | 11801         | A01-N2     | ✅     |
| Dark Chocolate  | 11802         | A01-N0     | ✅     |
| Ash Gray        | 11102         | A01-D3     | ✅     |
| Nardo Gray      | 11104         | A01-D0     | ✅     |
| Charcoal        | 11101         | A01-K1     | ✅     |

#### PLA Basic Gradient

| Color               | Filament Code | Variant ID | Status |
| ------------------- | ------------- | ---------- | ------ |
| Pink Citrus         | 10903         | A00-M3     | ✅     |
| Dusk Glare          | 10906         | A00-M6     | ✅     |
| Arctic Whisper      | 10900         | A00-M0     | ✅     |
| Solar Breeze        | 10901         | A00-M1     | ✅     |
| Blueberry Bubblegum | 10905         | A00-M5     | ✅     |
| Mint Lime           | 10904         | A00-M4     | ✅     |
| Ocean to Meadow     | 10902         | A00-M2     | ✅     |
| Cotton Candy Cloud  | 10907         | A00-M7     | ✅     |

#### PLA Glow

| Color  | Filament Code | Variant ID | Status |
| ------ | ------------- | ---------- | ------ |
| Green  | 15500         | A12-G0     | ✅     |
| Pink   | 15200         | A12-R0     | ✅     |
| Orange | 15300         | A12-A0     | ✅     |
| Yellow | 15400         | A12-Y0     | ✅     |
| Blue   | 15600         | A12-B0     | ✅     |

#### PLA Marble

| Color        | Filament Code | Variant ID | Status |
| ------------ | ------------- | ---------- | ------ |
| Red Granite  | 13201         | A07-R5     | ✅     |
| White Marble | 13103         | A07-D4     | ✅     |

#### PLA Aero

| Color | Filament Code | Variant ID | Status |
| ----- | ------------- | ---------- | ------ |
| White | 14102         | A11-W0     | ✅     |
| Gray  | 14104         | ?          | ❌     |
| Black | 14103         | A11-K0     | ✅     |

#### PLA Sparkle

| Color                | Filament Code | Variant ID | Status |
| -------------------- | ------------- | ---------- | ------ |
| Alpine Green Sparkle | 13501         | A08-G3     | ✅     |
| Slate Gray Sparkle   | 13102         | A08-D5     | ✅     |
| Royal Purple Sparkle | 13700         | A08-B7     | ✅     |
| Crimson Red Sparkle  | 13200         | A08-R2     | ✅     |
| Onyx Black Sparkle   | 13101         | A08-K2     | ✅     |
| Classic Gold Sparkle | 13402         | A08-Y1     | ✅     |

#### PLA Metal

| Color                 | Filament Code | Variant ID | Status |
| --------------------- | ------------- | ---------- | ------ |
| Cobalt Blue Metallic  | 13600         | A02-B2     | ✅     |
| Oxide Green Metallic  | 13500         | A02-G2     | ✅     |
| Iridium Gold Metallic | 13400         | A02-Y1     | ✅     |
| Copper Brown Metallic | 13800         | A02-N3     | ✅     |
| Iron Gray Metallic    | 13100         | A02-D2     | ✅     |

#### PLA Translucent

| Color         | Filament Code | Variant ID | Status |
| ------------- | ------------- | ---------- | ------ |
| Teal          | 13612         | ?          | ❌     |
| Blue          | 13611         | A17-B1     | ✅     |
| Orange        | 13301         | A17-A0     | ✅     |
| Purple        | 13710         | A17-P0     | ✅     |
| Red           | 13210         | A17-R0     | ✅     |
| Light Jade    | 13510         | A17-G0     | ✅     |
| Mellow Yellow | 13410         | A17-Y0     | ✅     |
| Cherry Pink   | 13211         | A17-R1     | ✅     |
| Ice Blue      | 13610         | ?          | ❌     |
| Lavender      | 13711         | A17-P1     | ✅     |

#### PLA Silk+

| Color       | Filament Code | Variant ID | Status |
| ----------- | ------------- | ---------- | ------ |
| Gold        | 13405         | A06-Y1     | ✅     |
| Titan Gray  | 13108         | A06-D0     | ✅     |
| Silver      | 13109         | A06-D1     | ✅     |
| White       | 13110         | A06-W0     | ✅     |
| Candy Red   | 13205         | A06-R0     | ✅     |
| Candy Green | 13506         | A06-G0     | ✅     |
| Mint        | 13507         | A06-G1     | ✅     |
| Blue        | 13604         | A06-B1     | ✅     |
| Baby Blue   | 13603         | A06-B0     | ✅     |
| Purple      | 13702         | A06-P0     | ✅     |
| Rose Gold   | 13206         | A06-R1     | ✅     |
| Pink        | 13207         | A06-R2     | ✅     |
| Champagne   | 13404         | A06-Y0     | ✅     |

#### PLA Silk Multi-Color

| Color          | Filament Code | Variant ID | Status |
| -------------- | ------------- | ---------- | ------ |
| Dawn Radiance  | 13912         | A05-M8     | ✅     |
| Aurora Purple  | 13909         | A05-M4     | ✅     |
| South Beach    | 13906         | A05-M1     | ✅     |
| Phantom Blue   | 13916         | ?          | ❌     |
| Mystic Magenta | 13913         | ?          | ❌     |
| Neon City      | 13903         | A05-T3     | ✅     |
| Midnight Blaze | 13902         | A05-T2     | ✅     |
| Gilded Rose    | 13901         | A05-T1     | ✅     |
| Blue Hawaii    | 13904         | A05-T4     | ✅     |
| Velvet Eclipse | 13905         | A05-T5     | ✅     |

#### PLA Galaxy

| Color   | Filament Code | Variant ID | Status |
| ------- | ------------- | ---------- | ------ |
| Purple  | 13602         | A15-B0     | ✅     |
| Green   | 13503         | A15-G0     | ✅     |
| Nebulae | 13504         | A15-G1     | ✅     |
| Brown   | 13203         | A15-R0     | ✅     |

#### PLA Wood

| Color         | Filament Code | Variant ID | Status |
| ------------- | ------------- | ---------- | ------ |
| Black Walnut  | 13107         | A16-K0     | ✅     |
| Rosewood      | 13204         | A16-R0     | ✅     |
| Clay Brown    | 13801         | A16-N0     | ✅     |
| Classic Birch | 13505         | A16-G0     | ✅     |
| White Oak     | 13106         | A16-W0     | ✅     |
| Ochre Yellow  | 13403         | A16-Y0     | ✅     |

#### PLA-CF

| Color        | Filament Code | Variant ID | Status |
| ------------ | ------------- | ---------- | ------ |
| Burgundy Red | 14200         | ?          | ❌     |
| Matcha Green | 14500         | ?          | ❌     |
| Lava Gray    | 14101         | A50-D6     | ✅     |
| Jeans Blue   | 14600         | ?          | ❌     |
| Black        | 14100         | A50-K0     | ✅     |
| Royal Blue   | 14601         | A50-B6     | ❌     |
| Iris Purple  | 14700         | ?          | ❌     |

#### PLA Tough+

| Color  | Filament Code | Variant ID | Status |
| ------ | ------------- | ---------- | ------ |
| Black  | 12104         | A10-K0     | ✅     |
| White  | 12107         | A10-W0     | ✅     |
| Yellow | 12401         | ?          | ❌     |
| Orange | 12301         | ?          | ❌     |
| Gray   | 12105         | A10-D0     | ✅     |
| Silver | 12106         | ?          | ❌     |
| Cyan   | 12601         | ?          | ❌     |

#### PLA Tough

| Color         | Filament Code | Variant ID | Status |
| ------------- | ------------- | ---------- | ------ |
| Lavender Blue | 12005         | A09-B5     | ✅     |
| Light Blue    | 12004         | A09-B4     | ✅     |
| Orange        | 12002         | A09-A0     | ✅     |
| Silver        | 12001         | A09-D1     | ✅     |
| Vermilion Red | 12003         | A09-R3     | ✅     |
| Yellow        | 12000         | A09-Y0     | ✅     |

### PETG

#### PETG HF

| Color        | Filament Code | Variant ID | Status |
| ------------ | ------------- | ---------- | ------ |
| Black        | 33102         | G02-K0     | ✅     |
| White        | 33100         | G02-W0     | ✅     |
| Red          | 33200         | G02-R0     | ✅     |
| Gray         | 33101         | G02-D0     | ✅     |
| Dark Gray    | 33103         | G02-D1     | ✅     |
| Cream        | 33401         | G02-Y1     | ✅     |
| Yellow       | 33400         | G02-Y0     | ✅     |
| Orange       | 33300         | G02-A0     | ✅     |
| Peanut Brown | 33801         | G02-N1     | ✅     |
| Lime Green   | 33501         | G02-G1     | ✅     |
| Green        | 33500         | G02-G0     | ✅     |
| Forest Green | 33502         | G02-G2     | ✅     |
| Lake Blue    | 33601         | G02-B1     | ✅     |
| Blue         | 33600         | G02-B0     | ✅     |

#### PETG Translucent

| Color                  | Filament Code | Variant ID | Status |
| ---------------------- | ------------- | ---------- | ------ |
| Translucent Teal       | 32501         | G01-G1     | ✅     |
| Translucent Light Blue | 32600         | G01-B0     | ✅     |
| Clear                  | 32101         | G01-C0     | ✅     |
| Translucent Gray       | 32100         | G01-D0     | ✅     |
| Translucent Olive      | 32500         | G01-G0     | ✅     |
| Translucent Brown      | 32800         | G01-N0     | ✅     |
| Translucent Orange     | 32300         | G01-A0     | ✅     |
| Translucent Pink       | 32200         | G01-P1     | ✅     |
| Translucent Purple     | 32700         | G01-P0     | ✅     |

#### PETG-CF

| Color           | Filament Code | Variant ID | Status |
| --------------- | ------------- | ---------- | ------ |
| Indigo Blue     | 31600         | ?          | ❌     |
| Malachite Green | 31500         | G50-G7     | ✅     |
| Titan Gray      | 31101         | G50-D6     | ✅     |
| Brick Red       | 31200         | ?          | ❌     |
| Violet Purple   | 31700         | G50-P7     | ✅     |
| Black           | 31100         | G50-K0     | ✅     |

### ABS

#### ABS

| Color            | Filament Code | Variant ID | Status |
| ---------------- | ------------- | ---------- | ------ |
| Silver           | 40102         | B00-D1     | ✅     |
| Black            | 40101         | B00-K0     | ✅     |
| White            | 40100         | B00-W0     | ✅     |
| Bambu Green      | 40500         | B00-G6     | ✅     |
| Olive            | 40502         | B00-G7     | ✅     |
| Tangerine Yellow | 40402         | B00-Y1     | ✅     |
| Orange           | 40300         | B00-A0     | ✅     |
| Red              | 40200         | B00-R0     | ✅     |
| Azure            | 40601         | B00-B4     | ✅     |
| Blue             | 40600         | B00-B0     | ✅     |
| Navy Blue        | 40602         | B00-B6     | ✅     |

#### ABS-GF

| Color  | Filament Code | Variant ID | Status |
| ------ | ------------- | ---------- | ------ |
| Orange | 41300         | B50-A0     | ✅     |
| Green  | 41500         | B50-G0     | ❌     |
| Red    | 41200         | B50-R0     | ❌     |
| Yellow | 41400         | ?          | ❌     |
| Blue   | 41600         | ?          | ❌     |
| White  | 41100         | B50-W0     | ❌     |
| Gray   | 41102         | ?          | ❌     |
| Black  | 41101         | B50-K0     | ✅     |

### ASA

#### ASA

| Color | Filament Code | Variant ID | Status |
| ----- | ------------- | ---------- | ------ |
| White | 45100         | B01-W0     | ✅     |
| Green | 45500         | ?          | ❌     |
| Black | 45101         | B01-K0     | ✅     |
| Gray  | 45102         | B01-D0     | ✅     |
| Red   | 45200         | B01-R0     | ✅     |
| Blue  | 45600         | ?          | ❌     |

#### ASA Aero

| Color | Filament Code | Variant ID | Status |
| ----- | ------------- | ---------- | ------ |
| White | 46100         | B02-W0     | ✅     |

#### ASA-CF

| Color | Filament Code | Variant ID | Status |
| ----- | ------------- | ---------- | ------ |
| Black | 46101         | B51-K0     | ✅     |

### PC

#### PC

| Color       | Filament Code | Variant ID | Status |
| ----------- | ------------- | ---------- | ------ |
| Transparent | 60103         | C00-C1     | ✅     |
| Clear Black | 60102         | C00-C0     | ✅     |
| Black       | 60101         | C00-K0     | ✅     |
| White       | 60100         | C00-W0     | ✅     |

#### PC FR

| Color | Filament Code | Variant ID | Status |
| ----- | ------------- | ---------- | ------ |
| Black | 63100         | C01-K0     | ✅     |
| White | 63101         | C01-W0     | ✅     |
| Gray  | 63102         | C01-D0     | ✅     |

### TPU

#### TPU for AMS

| Color      | Filament Code | Variant ID | Status |
| ---------- | ------------- | ---------- | ------ |
| Blue       | 53600         | U02-B0     | ✅     |
| Red        | 53200         | ?          | ❌     |
| Yellow     | 53400         | ?          | ❌     |
| Neon Green | 53500         | ?          | ❌     |
| White      | 53100         | ?          | ❌     |
| Gray       | 53102         | U02-D0     | ✅     |
| Black      | 53101         | U02-K0     | ✅     |

### PA

#### PAHT-CF

| Color | Filament Code | Variant ID | Status |
| ----- | ------------- | ---------- | ------ |
| Black | 70100         | N04-K0     | ✅     |

#### PA6-GF

| Color  | Filament Code | Variant ID | Status |
| ------ | ------------- | ---------- | ------ |
| Blue   | 72600         | ?          | ❌     |
| Orange | 72200         | ?          | ❌     |
| Yellow | 72400         | ?          | ❌     |
| Lime   | 72500         | ?          | ❌     |
| Brown  | 72800         | ?          | ❌     |
| White  | 72102         | ?          | ❌     |
| Gray   | 72103         | ?          | ❌     |
| Black  | 72104         | N08-K0     | ✅     |

### Support Material

#### Support for PLA/PETG

| Color  | Filament Code | Variant ID           | Status |
| ------ | ------------- | -------------------- | ------ |
| Nature | 65102         | S02-W0 (Old: S00-W0) | ✅     |
| Black  | 65103         | S05-C0               | ✅     |

#### Support for PLA (New Version)

| Color | Filament Code | Variant ID | Status |
| ----- | ------------- | ---------- | ------ |
| White | 65104         | S02-W1     | ✅     |

#### Support for ABS

| Color | Filament Code | Variant ID | Status |
| ----- | ------------- | ---------- | ------ |
| White | 66100         | S06-W0     | ✅     |

#### Support for PA/PET

| Color | Filament Code | Variant ID | Status |
| ----- | ------------- | ---------- | ------ |
| Green | 65500         | S03-G1     | ✅     |

#### PVA

| Color | Filament Code | Variant ID | Status |
| ----- | ------------- | ---------- | ------ |
| Clear | 66400         | S04-Y0     | ✅     |

## History

When Bambu Lab released the AMS for their 3D printers, it featured an RFID reader which could read RFID tags embedded on their filament spools to automatically update details such as material type, color and amount of remaining filament. However, the RFID tags were read-protected by keys, signed with an RSA2048 signature and structured in a proprietary format, which meant that only Bambu Lab could create these particular RFID tags and they could only be used on Bambu Lab printers. This led to the start of the [Bambu Research Group and a project to reverse engineer the RFID tag format](https://github.com/queengooborg/Bambu-Lab-RFID-Tag-Guide) in order to develop an open standard for all filament manufacturers and printers.

Of course, to research the tag format, a lot of tag data was required. This led to a community effort to scan lots of tags and cross-reference the data with known details about each spool. Eventually, enough of the format was reverse engineered to be able to determine what an open standard would need. But, the tag scanning didn't stop there, as the community realized another benefit to the collection of tags: even though custom tags couldn't be created due to the signing of the data, the data could be _cloned_ onto new tags and used to tell Bambu Lab printers what material and color a spool was, just like Bambu Lab first-party spools.

Originally, the collection of scanned tags was kept private as the research group was not sure if Bambu Lab would react negatively to sniffing data transfers to obtain hidden keys. However, as time progressed and new methods were discovered to obtain tag data, the group slowly opened up the tag collection and made it easier to access, until eventually it became the consensus to create this repository.
