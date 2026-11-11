# Fleet Intelligence design system

This document records the visual rules used by the Streamlit interface. The goal is a
quiet operations workspace: clear hierarchy, restrained color, and controls that remain
easy to scan during a busy shift.

## Tokens

### Color

| Token | Value | Use |
|---|---|---|
| `--fi-bg` | `#121514` | Main application background |
| `--fi-panel` | `#191D1B` | Sidebar, cards, forms, and chart surfaces |
| `--fi-raised` | `#212724` | Hover, selected, and nested surfaces |
| `--fi-line` | `#333A36` | Dividers, borders, and table outlines |
| `--fi-text` | `#ECEDE6` | Main text and values |
| `--fi-muted` | `#A8AFA6` | Supporting text, labels, and metadata |
| `--fi-disabled` | `#6F766D` | Disabled controls |
| `--fi-ochre` | `#D69A4A` | Primary action, focus, and current selection |
| `--fi-sage` | `#8FA37A` | Healthy, available, or completed state |
| `--fi-rust` | `#C77658` | Overdue work, errors, or attention |
| `--fi-blue` | `#7D9AA5` | In-transit and informational state |

Color is a cue, not the only way a state is communicated. Status labels and explanatory
text stay visible alongside colored dots, borders, bars, or map marks.

### Type

The interface uses Bahnschrift when installed, then falls back to Aptos and the system UI
font. Cascadia Code or Consolas is reserved for IDs, timestamps, and other compact values.

| Style | Size / line height | Use |
|---|---:|---|
| Display | 28 / 32 px | Page hero title |
| H1 | 22 / 28 px | Page title |
| H2 | 18 / 24 px | Section heading |
| Body | 14 / 22 px | Main content, labels, and controls |
| Caption | 12 / 18 px | Supporting details and timestamps |

### Spacing and corners

Use the spacing scale in multiples of four: `4`, `8`, `12`, `16`, `24`, and `32` px.
Small controls use a 4 px radius, cards use 6 px, and dialogs use 8 px.

## Component examples

- **Page header:** H1 title followed by a muted, one-line description.
- **Command Center hero:** Display title inside a panel with a narrow ochre leading edge.
- **Metric:** Main value in the display numeric style; label remains visible above it.
- **Workspace selection:** Panel surface with a clear ochre selected border and a text label.
- **Primary action:** Ochre fill with dark text. Secondary actions use the panel surface and
  a visible border.
- **Operational alert:** Rust edge plus a title and a short explanation or next action.
- **Forms and tables:** Panel background, consistent line color, and labels that identify
  the affected field or record.

The main styles and CSS tokens live in `components/theme.py`; Streamlit's base colors are
set in `.streamlit/config.toml`.

## Accessibility rules

1. Keep normal text at 12 px or larger and use the specified line heights for readability.
2. Preserve readable text/background contrast; do not use muted or disabled text for
   essential instructions or values.
3. Pair status colors with text or an icon/shape so color is never the only signal.
4. Keep keyboard focus visible with a 2 px ochre outline and offset.
5. Give controls descriptive labels and preserve native keyboard behavior.
6. Do not communicate an error, success, or selection through color alone.

## Map data note

Truck map markers are illustrative random points along their assigned routes. They move
on page refresh and on the ten-minute automatic map refresh. They are not live telematics
or GPS positions.
