from streamlit.testing.v1 import AppTest


def test_welcome_dialog_appears_then_stays_dismissed_for_session():
    app = AppTest.from_string('''\
from components.welcome import show_welcome
show_welcome()
''').run()

    assert app.button[0].label == "Get started"
    assert any("illustrative points" in item.value for item in app.info)

    app.button[0].click().run()
    assert not any(button.label == "Get started" for button in app.button)

    app.run()
    assert not any(button.label == "Get started" for button in app.button)
