# Bambu Lab RFID Library

This repository contains a collection of RFID tag scans from Bambu Lab filament spools. The data can be used to create cloned tags for Bambu Lab printers or for research purposes.

For more information about Bambu Lab RFID tags and their format, see https://github.com/queengooborg/Bambu-Lab-RFID-Tag-Guide.

## Viewing Tag Data

A script is included in this repository, `parse.py`, that will parse a tag dump and extract its information in an easy-to-read terminal output and easy-to-parse JSON format.  To run it, simply run `python3 parse.py [/path/to/tag.bin-or-json]`.

## Contributing

The best way to contribute is to provide data for Bambu Lab RFID tags. Not sure how to obtain the data? Check out the [guide written in the Bambu Lab RFID Tag Guide repository](https://github.com/queengooborg/Bambu-Lab-RFID-Tag-Guide/blob/main/docs/ReadTags.md)!

Tags are stored in the following folder structure: `Material Category` > `Material Name` > `Color Name` > `Tag UID` > `Tag Files`

## Filament Data

See the complete [Bambu Lab Filament DataSheet](./bambulab_filament_datasheet.md) for all filament codes, colors, and variant IDs.

## History

When Bambu Lab released the AMS for their 3D printers, it featured an RFID redear which could read RFID tags embedded on their filament spools to automatically update details such as material type, color and amount of remaining filament. However, the RFID tags were read-protected by keys, signed with an RSA2048 signature and structured in a proprietary format, which meant that only Bambu Lab could create these particular RFID tags and they could only be used on Bambu Lab printers. This led to the start of the [Bambu Research Group and a project to reverse engineer the RFID tag format](https://github.com/queengooborg/Bambu-Lab-RFID-Tag-Guide) in order to develop an open standard for all filament manufacturers and printers.

Of course, to research the tag format, a lot of tag data was required. This led to a community effort to scan lots of tags and cross-reference the data with known details about each spool. Eventually, enough of the format was reverse engineered to be able to determine what an open standard would need. But, the tag scanning didn't stop there, as the community realized another benefit to the collection of tags: even though custom tags couldn't be created due to the signing of the data, the data could be _cloned_ onto new tags and used to tell Bambu Lab printers what material and color a spool was, just like Bambu Lab first-party spools.

Originally, the collection of scanned tags was kept private as the research group was not sure if Bambu Lab would react negatively to sniffing data transfers to obtain hidden keys. However, as time progressed and new methods were discovered to obtain tag data, the group slowly opened up the tag collection and made it easier to access, until eventually it became the consensus to create this repository.
