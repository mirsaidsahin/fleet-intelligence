# Definitions

These definitions are the contract for every status, KPI and image the app shows.

## Truck and driver status

The database has no status column on `trucks` or `drivers`. Status is derived from
open jobs (`jobs.Status` of `Pending` or `In Transit`). Completed and Cancelled jobs are ignored.
Trucks group jobs by `jobs.TruckID`; drivers group by `jobs.DriverID`.

| Status | Rule |
|---|---|
| Conflict | Two or more open jobs whose time windows overlap, or more than one In Transit job |
| In Transit | At least one In Transit job and no conflict |
| Needs Review | No In Transit job, and a Pending job whose `StartDate` has already passed |
| Scheduled | Pending jobs only, all starting now or later (a Pending job with no `StartDate` counts here) |
| Available | No Pending and no In Transit job on record |

Priority: Conflict, In Transit, Needs Review, Scheduled, Available.

- A job's time window runs from `StartDate` to `StartDate` plus the route's `EstimatedHours`.
- An In Transit job has no `EndDate`, so its window extends to the current time when it has outrun the estimate.
- A job with no `StartDate` cannot be placed on a timeline and is skipped in the overlap check.
- Available means "nothing open in the database". It does not confirm maintenance, rest time or dispatch readiness, which the schema does not record.
- Dates in MySQL carry no time zone. They are compared with the application's local time.

Values from the 2026-10-29 dump, as a hand check for Phase 5: 2 In Transit (trucks 21 and 24),
7 Needs Review (trucks 1, 2, 4, 5, 9, 29, 30), 21 Available.

## Command Center indicators

- Open jobs count Pending and In Transit records.
- Pending past start counts Pending records with a `StartDate` before MySQL `NOW()`.
- Fleet in transit is the number of trucks with an In Transit job divided by all trucks.
- The route network draws the routes from MySQL. Node positions are approximate city coordinates
  stored in the dashboard for an offline schematic; route distance and open-job counts remain database values.
- Dispatch alerts are raised when a Pending job's start is past or an In Transit job's elapsed
  time is greater than its route estimate. They are review prompts, not claims about GPS position.
- Driver on-time rate compares each completed job's recorded `EndDate` with `StartDate` plus
  the route's `EstimatedHours`; the scorecard also sums recorded revenue and route distance.

## Trailer image convention

The database stores no trailers. The tractor-with-trailer image is a visual convention only:
it is shown when `trucks.RequiredLicense` is `CE` and the truck has an In Transit job.
Every other truck shows the tractor-only image. The UI labels these images as illustrative
(`services/visual_config.py`, `VISUAL_CONVENTION_NOTE`). No trailer ID, owner or assignment is ever displayed.

## Image assets

ETS2 portraits, brand logos and truck images stay out of the public repository.
`.gitignore` ignores everything under `assets/drivers`, `assets/brands` and `assets/trucks`
except the `.gitkeep` markers. See `assets/README.md` for naming.
