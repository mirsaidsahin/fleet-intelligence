"""System health details."""
from components.bootstrap import get_app_context
from components.health_panels import connection_card
from components.status_bar import current_status, last_success_at
from components.ui import page_header

ctx = get_app_context()
status = current_status(ctx)

page_header("System", "Database connection status")
connection_card(status, last_success_at(), ctx.settings)
