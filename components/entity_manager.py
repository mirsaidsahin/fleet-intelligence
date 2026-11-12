"""Reusable searchable table and safe create, edit and delete forms."""
from __future__ import annotations

from datetime import date, datetime

import pandas as pd
import streamlit as st

from repositories.fleet import FleetRepository
from services.image_assets import brand_image, driver_image, save_uploaded_image, truck_image
from services.input_validation import FIELDS, validate_record
from services.visual_config import VISUAL_CONVENTION_NOTE, choose_visual_config
from utils.db import DatabaseUnavailableError, QueryError

LOOKUPS = {
    "brand": ("brands","BrandName"), "garage": ("garages","City"), "driver": ("drivers","FirstName"),
    "truck": ("trucks","PlateNumber"), "cargo": ("cargos","CargoName"), "route": ("routes","DepartureCity"),
    "customer": ("customers","CompanyName"),
}


def _label(kind: str, row: dict) -> str:
    if kind == "driver":
        return f"{row.get('FirstName','')} {row.get('LastName','')} (#{row['id']})"
    if kind == "route":
        return f"{row.get('label','')} → #{row['id']}"
    return f"{row.get('label','')} (#{row['id']})"


def _read_form(repo: FleetRepository, table: str, current: dict | None) -> dict:
    values = {}
    for name, kind, nullable in FIELDS[table]:
        value = (current or {}).get(name)
        label = name.replace("ID", "").replace("EUR", " (EUR)").replace("Kg", " (kg)")
        if kind in LOOKUPS:
            lookup, label_col = LOOKUPS[kind]
            options = repo.options(lookup, FleetRepository.TABLES[lookup][0], label_col)
            choices = ([None] if nullable else []) + [int(row["id"]) for row in options]
            labels = {int(row["id"]): _label(kind, row) for row in options}
            index = choices.index(value) if value in choices else 0
            selected = st.selectbox(label, choices, index=index, format_func=lambda x: "None" if x is None else labels.get(x, str(x)), key=f"form_{table}_{name}")
            values[name] = selected
        elif kind == "license":
            choices = ["C", "CE"]
            values[name] = st.selectbox(label, choices, index=choices.index(value) if value in choices else 0, key=f"form_{table}_{name}")
        elif kind == "status":
            choices = ["Pending", "In Transit", "Completed", "Cancelled"]
            values[name] = st.selectbox(label, choices, index=choices.index(value) if value in choices else 0, key=f"form_{table}_{name}")
        elif kind == "datetime":
            dt = value if isinstance(value, datetime) else None
            enabled = st.checkbox(f"Set {label}", value=dt is not None, key=f"set_{table}_{name}")
            if enabled:
                day = st.date_input(label + " date", value=dt.date() if dt else date.today(), key=f"date_{table}_{name}")
                tm = st.time_input(label + " time", value=dt.time().replace(second=0, microsecond=0) if dt else datetime.now().time().replace(second=0, microsecond=0), key=f"time_{table}_{name}")
                values[name] = datetime.combine(day, tm)
            else:
                values[name] = None
        elif kind == "int":
            default = int(value or 0)
            values[name] = st.number_input(label, min_value=0, value=default, step=1, key=f"form_{table}_{name}")
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


def entity_manager(database, table: str, title: str) -> None:
    repo = FleetRepository(database)
    st.subheader(title)
    notice_key = f"record_notice_{table}"
    if notice_key in st.session_state:
        st.success(st.session_state.pop(notice_key))
    image_notice_key = f"image_notice_{table}"
    if image_notice_key in st.session_state:
        st.success(st.session_state.pop(image_notice_key))
    try:
        rows = repo.rows(table)
        if not rows:
            st.info("No records found. Add the first record below.")
        else:
            frame = pd.DataFrame(rows)
            search = st.text_input("Search records", key=f"search_{table}", placeholder="Search any visible value")
            if search.strip():
                mask = frame.astype(str).apply(lambda col: col.str.contains(search.strip(), case=False, na=False)).any(axis=1)
                frame = frame[mask]
            st.caption(f"{len(frame)} record(s) shown · maximum 500")
            st.dataframe(frame, hide_index=True, width="stretch")
            if table in ("trucks", "drivers", "brands"):
                key_col = FleetRepository.TABLES[table][0]
                selected_id = st.selectbox("Image preview", [int(row[key_col]) for row in rows], format_func=lambda x: f"#{x}", key=f"image_preview_{table}")
                selected = next(row for row in rows if int(row[key_col]) == selected_id)
                if table == "drivers":
                    image_path = driver_image(selected_id)
                elif table == "brands":
                    image_path = brand_image(selected_id)
                    visual = None
                else:
                    transit = database.fetch_one(
                        "SELECT DriverID FROM jobs WHERE TruckID=:id AND Status='In Transit' ORDER BY StartDate DESC LIMIT 1",
                        {"id": selected_id},
                    )
                    visual = choose_visual_config(selected.get("RequiredLicense"), bool(transit)).value
                    image_path = truck_image(selected_id, selected.get("BrandID"), visual)
                    driver_id = transit.get("DriverID") if transit else selected.get("AssignedDriverID")
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
                if image_path and table != "trucks":
                    st.image(str(image_path), width=144)
                else:
                    if table != "trucks":
                        st.caption("No local image. See assets/README.md for supported filenames.")
                uploader_types = ["png"] if table in ("brands", "trucks") else ["png", "jpg", "jpeg"]
                upload = st.file_uploader(
                    "Add or replace image (max 10 MB)",
                    type=uploader_types,
                    max_upload_size=10,
                    key=f"upload_{table}_{selected_id}",
                )
                if upload is not None:
                    st.caption(f"Selected: {upload.name}")
                if st.button("Save image", key=f"save_image_{table}_{selected_id}", disabled=upload is None):
                    try:
                        saved = save_uploaded_image(table, selected_id, upload.getvalue(), visual if table == "trucks" else None)
                        st.session_state[image_notice_key] = f"Image saved: {saved.name}"
                        st.rerun()
                    except (ValueError, OSError) as exc:
                        st.error(str(exc))
        key_col = FleetRepository.TABLES[table][0]
        all_rows = rows
        options = [int(row[key_col]) for row in all_rows]
        with st.expander("Create or edit record", expanded=not bool(rows)):
            mode = st.radio("Action", ["Create", "Edit"], horizontal=True, key=f"mode_{table}")
            current = None
            if mode == "Edit":
                if not options:
                    st.info("There are no records to edit.")
                else:
                    record_id = st.selectbox("Record", options, format_func=lambda x: f"#{x}", key=f"edit_id_{table}")
                    current = next(row for row in all_rows if int(row[key_col]) == record_id)
            with st.form(f"save_{table}"):
                values = _read_form(repo, table, current)
                submitted = st.form_submit_button("Save record", type="primary", disabled=(mode == "Edit" and current is None))
            if submitted:
                problems = validate_record(table, values, FIELDS, current if table == "jobs" else None)
                conflicts = []
                if table == "jobs" and not problems:
                    conflicts = repo.assignment_conflicts(values, int(current[key_col]) if current else None)
                    if conflicts:
                        refs = ", ".join(f"#{job['JobID']} ({job['Status']})" for job in conflicts)
                        problems.append(f"This truck or driver has an overlapping open job: {refs}.")
                if problems:
                    for problem in problems:
                        st.error(problem)
                else:
                    try:
                        repo.save(table, values, int(current[key_col]) if mode == "Edit" and current else None)
                        if current:
                            changed = [name for name in values if current.get(name) != values[name]]
                            summary = record_change_summary(title, "Updated", int(current[key_col]), changed)
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
                delete_id = st.selectbox("Record to delete", options, format_func=lambda x: f"#{x}", key=f"delete_id_{table}")
                if delete_record_controls(title, int(delete_id), repo.linked_record_counts(table, int(delete_id)), table):
                    try:
                        repo.delete(table, int(delete_id))
                        st.session_state[notice_key] = record_change_summary(title, "Deleted", int(delete_id))
                        st.rerun()
                    except (QueryError, DatabaseUnavailableError) as exc:
                        st.error(str(exc))
    except (QueryError, DatabaseUnavailableError) as exc:
        st.error(str(exc))
    except Exception:
        st.error("Could not load records. Check the application log for details.")
