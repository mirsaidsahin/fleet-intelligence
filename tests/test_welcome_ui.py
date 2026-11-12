from streamlit.testing.v1 import AppTest


def test_welcome_dialog_appears_then_stays_dismissed_for_session():
    app = AppTest.from_string('''\
from components.welcome import show_welcome
show_welcome()
''').run()

    assert app.button[0].label == "Get started"
    assert app.subheader[0].value == "Fleet and dispatch, at a glance"
    disclaimer = app.info[0].value
    assert "not live tracking" in disclaimer
    assert "non-commercial school project" in disclaimer
    assert "Trademarks belong to their respective owners" in disclaimer

    app.button[0].click().run()
    assert not any(button.label == "Get started" for button in app.button)

    app.run()
    assert not any(button.label == "Get started" for button in app.button)
