"""Streamlit AppTest checks for the delete confirmation and impact UI."""
from streamlit.testing.v1 import AppTest


def make_app(linked_counts):
    return AppTest.from_string(f'''\
from components.entity_manager import delete_record_controls, record_change_summary
if delete_record_controls("Truck", 12, {linked_counts!r}, "truck"):
    import streamlit as st
    st.success("Delete action requested")
''')


def test_linked_records_are_shown_and_disable_delete_even_after_confirmation():
    app = make_app({"jobs": 2}).run()

    assert "2 jobs" in app.warning[0].value
    assert app.button[0].label == "Delete"
    assert app.button[0].disabled

    app.checkbox[0].check().run()
    assert app.button[0].disabled
    assert not app.success


def test_unlinked_record_requires_confirmation_then_enables_delete():
    app = make_app({}).run()

    assert "No linked records" in app.caption[0].value
    assert app.button[0].disabled

    app.checkbox[0].check().run()
    assert not app.button[0].disabled
    app.button[0].click().run()
    assert app.success[0].value == "Delete action requested"


def test_success_summary_names_updated_record_and_changed_fields():
    app = AppTest.from_string('''\
import streamlit as st
from components.entity_manager import record_change_summary
st.success(record_change_summary("Truck", "Updated", 12, ["Model", "Mileage"]))
''').run()

    assert app.success[0].value == "Updated truck record #12. Changed: Model, Mileage."
