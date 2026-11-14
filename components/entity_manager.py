"""Reusable searchable table and safe create, edit and delete forms."""
from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from components.tables import search_frame
from repositories.fleet import FleetRepository
from services.image_assets import brand_image, driver_image, save_uploaded_image, truck_image
from services.input_validation import FIELDS, validate_record
from services.visual_config import VISUAL_CONVENTION_NOTE, choose_visual_config
from utils.db import DatabaseUnavailableError, QueryError

LOOKUPS = {
    # Map form relationship types to their source table and display column.
    "brand": ("brands","BrandName"), "garage": ("garages","City"), "driver": ("drivers","FirstName"),
    "truck": ("trucks","PlateNumber"), "cargo": ("cargos","CargoName"), "route": ("routes","DepartureCity"),
    "customer": ("customers","CompanyName"),
}
# Fixed-choice fields and the values their select boxes offer.
CHOICES = {
    "license": ["C", "CE"],
    "status": ["Pending", "In Transit", "Completed", "Cancelled"],
}
IMAGE_TABLES = ("trucks", "drivers", "brands")


def _label(kind: str, row: dict) -> str:
    """Format a relationship option with a readable label and its database id."""
    if kind == "driver":
        return f"{row.get('FirstName','')} {row.get('LastName','')} (#{row['id']})"
    if kind == "route":
        return f"{row.get('label','')} → #{row['id']}"
    return f"{row.get('label','')} (#{row['id']})"


def _read_form(repo: FleetRepository, table: str, current: dict | None) -> dict:
    """Render fields for one entity and collect their current form values."""
    values = {}
    # The field metadata selects the appropriate Streamlit input widget.
    for name, kind, nullable in FIELDS[table]:
        value = (current or {}).get(name)
        label = name.replace("ID", "").replace("EUR", " (EUR)").replace("Kg", " (kg)")
        if kind in LOOKUPS:
            lookup, label_col = LOOKUPS[kind]
            options = repo.options(lookup, FleetRepository.TABLES[lookup][0], label_col)
            choices = ([None] if nullable else []) + [int(row["id"]) for row in options]
            # Keep ids as stored values while showing human-readable labels.
            labels = {int(row["id"]): _label(kind, row) for row in options}
            index = choices.index(value) if value in choices else 0
            values[name] = st.selectbox(label, choices, index=index, format_func=lambda x: "None" if x is None else labels.get(x, str(x)), key=f"form_{table}_{name}")
        elif kind in CHOICES:
            choices = CHOICES[kind]
            values[name] = st.selectbox(label, choices, index=choices.index(value) if value in choices else 0, key=f"form_{table}_{name}")
        elif kind == "datetime":
            # Optional date/time fields use a checkbox so NULL stays explicit.
            dt = value if isinstance(value, datetime) else None
            enabled = st.checkbox(f"Set {label}", value=dt is not None, key=f"set_{table}_{name}")
            if enabled:
                default = (dt or datetime.now()).replace(second=0, microsecond=0)
                day = st.date_input(label + " date", value=default.date(), key=f"date_{table}_{name}")
                tm = st.time_input(label + " time", value=default.time(), key=f"time_{table}_{name}")
                values[name] = datetime.combine(day, tm)
            else:
                values[name] = None
        elif kind == "int":
            values[name] = st.number_input(label, min_value=0, value=int(value or 0), step=1, key=f"form_{table}_{name}")
        elif kind == "decimal":
            values[name] = st.number_input(label, min_value=0.0, value=float(value or 0), step=0.1, key=f"form_{table}_{name}")
        else:
            values[name] = st.text_input(label, value="" if value is None else str(value), key=f"form_{table}_{name}")
            if nullable and not values[name].strip():
                values[name] = None
    return values


def delete_record_controls(title: str, record_id: int, linked_counts: dict[str, int], key: str) -> bool:
    """Render a linked-record impact warning and explicit delete confirmation."""
    linked = {name: count for name, count in linked_counts.items() if count}
    total_linked = sum(linked.values())
    if linked:
        st.warning("Deletion is blocked by linked records: " + ", ".join(
            f"{count} {name}" for name, count in linked.items()
        ) + ". Remove or reassign them first.")
    else:
        st.caption("No linked records were found.")
    confirm = st.checkbox(f"I confirm deletion of {title.lower()} record #{record_id}.", key=f"confirm_{key}")
    return st.button("Delete", key=f"delete_{key}", disabled=(not confirm or total_linked > 0))


def record_change_summary(title: str, operation: str, record_id: int | None = None, changed_fields: list[str] | None = None) -> str:
    """Describe a completed record change for the post-rerun success notice."""
    subject = f"{title.lower()} record" + (f" #{record_id}" if record_id is not None else "")
    summary = f"{operation.capitalize()} {subject}."
    if operation == "Updated" and changed_fields:
        summary += " Changed: " + ", ".join(changed_fields) + "."
    return summary


def _truck_preview(database, truck: dict, truck_id: int) -> str:
    """Show a truck with its current or assigned driver; return the visual variant used."""
    # Truck imagery reflects its demo status and selected driver.
    transit = database.fetch_one(
        "SELECT DriverID FROM jobs WHERE TruckID=:id AND Status='In Transit' ORDER BY StartDate DESC LIMIT 1",
        {"id": truck_id},
    )
    visual = choose_visual_config(truck.get("RequiredLicense"), bool(transit)).value
    image_path = truck_image(truck_id, truck.get("BrandID"), visual)
    driver_id = transit.get("DriverID") if transit else truck.get("AssignedDriverID")
    driver_path = driver_image(int(driver_id)) if driver_id else None
    driver = database.fetch_one(
        "SELECT CONCAT(FirstName, ' ', LastName) AS name FROM drivers WHERE DriverID=:id",
        {"id": driver_id},
    ) if driver_id else None
    st.caption(VISUAL_CONVENTION_NOTE)
    vehicle_col, driver_col = st.columns([3, 1], vertical_alignment="center")
    with vehicle_col:
        if image_path:
            st.image(str(image_path), width=360)
            st.caption("Truck")
        else:
            st.caption("No truck image. See assets/README.md for supported filenames.")
    with driver_col:
        if driver_path:
            st.image(str(driver_path), width=128)
            st.caption("Current driver" if transit else "Assigned driver")
        else:
            st.caption("No driver photo")
        if driver:
            st.caption(driver["name"])
    return visual


def _image_panel(database, table: str, rows: list[dict], key_col: str, notice_key: str) -> None:
    """Preview one record's local image and let the user add or replace it."""
    selected_id = st.selectbox("Image preview", [int(row[key_col]) for row in rows], format_func=lambda x: f"#{x}", key=f"image_preview_{table}")
    visual = None
    if table == "trucks":
        selected = next(row for row in rows if int(row[key_col]) == selected_id)
        visual = _truck_preview(database, selected, selected_id)
    else:
        image_path = driver_image(selected_id) if table == "drivers" else brand_image(selected_id)
        if image_path:
            st.image(str(image_path), width=144)
        else:
            st.caption("No local image. See assets/README.md for supported filenames.")
    upload = st.file_uploader(
        "Add or replace image (max 10 MB)",
        type=["png", "jpg", "jpeg"] if table == "drivers" else ["png"],
        max_upload_size=10,
        key=f"upload_{table}_{selected_id}",
    )
    if upload is not None:
        st.caption(f"Selected: {upload.name}")
    if st.button("Save image", key=f"save_image_{table}_{selected_id}", disabled=upload is None):
        try:
            saved = save_uploaded_image(table, selected_id, upload.getvalue(), visual)
            st.session_state[notice_key] = f"Image saved: {saved.name}"
            st.rerun()
        except (ValueError, OSError) as exc:
            st.error(str(exc))


def entity_manager(database, table: str, title: str) -> None:
    """Render search, image, create/edit, and delete controls for one table."""
    repo = FleetRepository(database)
    st.subheader(title)
    # Notices are stored before a rerun and shown once on the refreshed page.
    notice_key = f"record_notice_{table}"
    image_notice_key = f"image_notice_{table}"
    for key in (notice_key, image_notice_key):
        if key in st.session_state:
            st.success(st.session_state.pop(key))
    key_col = FleetRepository.TABLES[table][0]
    try:
        # Load a bounded set of rows once for the table, editor, and image picker.
        rows = repo.rows(table)
        if not rows:
            st.info("No records found. Add the first record below.")
        else:
            search = st.text_input("Search records", key=f"search_{table}", placeholder="Search any visible value")
            # Search every visible column without changing the stored rows.
            frame = search_frame(pd.DataFrame(rows), search)
            st.caption(f"{len(frame)} record(s) shown · maximum 500")
            st.dataframe(frame, hide_index=True, width="stretch")
            if table in IMAGE_TABLES:
                _image_panel(database, table, rows, key_col, image_notice_key)
        options = [int(row[key_col]) for row in rows]
        with st.expander("Create or edit record", expanded=not rows):
            # Reuse one form for both insert and update actions.
            mode = st.radio("Action", ["Create", "Edit"], horizontal=True, key=f"mode_{table}")
            current = None
            if mode == "Edit":
                if not options:
                    st.info("There are no records to edit.")
                else:
                    record_id = st.selectbox("Record", options, format_func=lambda x: f"#{x}", key=f"edit_id_{table}")
                    current = next(row for row in rows if int(row[key_col]) == record_id)
            current_id = int(current[key_col]) if current else None
            with st.form(f"save_{table}"):
                values = _read_form(repo, table, current)
                submitted = st.form_submit_button("Save record", type="primary", disabled=(mode == "Edit" and current is None))
            if submitted:
                # Validate fields and job overlaps before sending any write query.
                problems = validate_record(table, values, FIELDS, current if table == "jobs" else None)
                if table == "jobs" and not problems:
                    conflicts = repo.assignment_conflicts(values, current_id)
                    if conflicts:
                        refs = ", ".join(f"#{job['JobID']} ({job['Status']})" for job in conflicts)
                        problems.append(f"This truck or driver has an overlapping open job: {refs}.")
                if problems:
                    for problem in problems:
                        st.error(problem)
                else:
                    try:
                        # Save, retain a short success notice, then refresh the table.
                        repo.save(table, values, current_id)
                        if current:
                            changed = [name for name in values if current.get(name) != values[name]]
                            summary = record_change_summary(title, "Updated", current_id, changed)
                        else:
                            summary = record_change_summary(title, "Created")
                        st.session_state[notice_key] = summary
                        st.rerun()
                    except (QueryError, DatabaseUnavailableError) as exc:
                        st.error(str(exc))
        with st.expander("Delete record"):
            if not options:
                st.info("There are no records to delete.")
            else:
                delete_id = int(st.selectbox("Record to delete", options, format_func=lambda x: f"#{x}", key=f"delete_id_{table}"))
                if delete_record_controls(title, delete_id, repo.linked_record_counts(table, delete_id), table):
                    try:
                        # The UI checks known links first; database constraints remain final.
                        repo.delete(table, delete_id)
                        st.session_state[notice_key] = record_change_summary(title, "Deleted", delete_id)
                        st.rerun()
                    except (QueryError, DatabaseUnavailableError) as exc:
                        st.error(str(exc))
    except (QueryError, DatabaseUnavailableError) as exc:
        st.error(str(exc))
    except Exception:
        st.error("Could not load records. Check the application log for details.")
