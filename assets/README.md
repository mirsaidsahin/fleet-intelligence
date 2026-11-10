# Image assets

Images are local files and are NOT committed to the public repository
(see `.gitignore`). You can upload or replace images from the Fleet and Drivers pages;
the app saves them here using the naming convention below. Direct file placement also works.

| Folder | Naming | Matches |
|---|---|---|
| `drivers/` | `{DriverID}.png`, `.jpg` or `.jpeg` | `drivers.DriverID` (1 to 30) |
| `brands/` | `{BrandID}.png` | `brands.BrandID` (1 to 11) |
| `trucks/` | `by_truck/{TruckID}_{tractor|trailer}.png`, `by_brand/{BrandID}_{tractor|trailer}.png`, `default_{tractor|trailer}.png` | resolved in that order |

Driver portraits accept PNG/JPEG. Brand logos and truck views accept PNG. Uploads are limited to 10 MB.
Truck uploads target the view required for that truck's current visual convention.

Brand logo files `{BrandID}.png` are currently populated for all eleven seeded
brands. The logo is centered on a light card so dark marks remain visible in the
dark interface. Sources, original formats and source pages:

| BrandID | Brand | Source |
|---:|---|---|
| 1 | Scania | [TOPpng Scania logo](https://toppng.com/show_download/463979/scania-auto-vector-logo-free) |
| 2 | Volvo | [Wikimedia Commons: Volvo Trucks Logo](https://commons.wikimedia.org/wiki/File:Volvo_Trucks_Logo.png) |
| 3 | MAN | [Wikimedia Commons: MAN Truck & Bus logo](https://commons.wikimedia.org/wiki/File:MAN_Truck_%26_Bus_-_Logo.svg) |
| 4 | Mercedes-Benz | [Wikimedia Commons: Mercedes-Benz Trucks logo](https://commons.wikimedia.org/wiki/File:Mercedes-Benz_Trucks_Logo.svg) |
| 5 | Renault | [Wikimedia Commons: Renault Trucks logo](https://commons.wikimedia.org/wiki/File:Renault_Trucks_logo.svg) |
| 6 | Mitsubishi | [Wikimedia Commons: Fuso logo](https://commons.wikimedia.org/wiki/File:Fuso_logo.svg) |
| 7 | Isuzu | [Wikimedia Commons: Isuzu logo](https://commons.wikimedia.org/wiki/File:Isuzu.svg) |
| 8 | Iveco | [Wikimedia Commons: Iveco Logo 2023](https://commons.wikimedia.org/wiki/File:Iveco_Logo_2023.svg) |
| 9 | Ford | [Wikimedia Commons: Ford logo](https://commons.wikimedia.org/wiki/File:Ford_logo.svg) |
| 10 | BMC | [Wikimedia Commons: BMC logo](https://commons.wikimedia.org/wiki/File:BMC_logo.svg) |
| 11 | DAF | [Wikimedia Commons: DAF logo](https://commons.wikimedia.org/wiki/File:DAF_logo.svg) |

Logo source and license details belong to their respective pages; brand marks
remain trademarks of their owners. The Scania image is offered for personal use
by its source, so keep it in this local coursework project and do not publish it
as a general-purpose asset. Logo images are excluded from Git by `.gitignore`.

Use images you have permission to use. Keep third-party artwork local and document
sources for anything you decide to publish.
