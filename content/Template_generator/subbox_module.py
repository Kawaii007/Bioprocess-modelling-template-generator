from ipywidgets import VBox, HBox, Layout, HTML, Label, Textarea
import os
import markdown

# Shared/global log content and shared widget
GLOBAL_LOG = ""
GLOBAL_LOG_WIDGET = None  # All subboxes will point to this

def load_readme_section(section_title, readme_path="README.md"):
    """Load a section from README.md, including context before the header, render Markdown to HTML."""
    if not os.path.exists(readme_path):
        return f"<i>README not found at {readme_path}</i>"

    with open(readme_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    section_lines = []
    capture = False
    for i, line in enumerate(lines):
        if line.strip().startswith("#") and section_title.lower() in line.lower():
            # Include lines before the header until an empty line or previous header
            j = i - 1
            while j >= 0 and not lines[j].strip().startswith("#") and lines[j].strip():
                section_lines.insert(0, lines[j])
                j -= 1
            # Include the header itself
            section_lines.append(line)
            capture = True
            continue

        if capture:
            # Stop at the next header
            if line.strip().startswith("#"):
                break
            section_lines.append(line)

    # Fallback: show top of file if section not found
    if not section_lines:
        section_lines = lines[:i]

    # Render Markdown to HTML
    html_content = markdown.markdown(
        "".join(section_lines),
        extensions=["fenced_code", "tables"]
    )

    return f"""
    <div style="
        border:1px solid #ccc;
        border-radius:6px;
        padding:10px;
        height:250px;
        overflow-y:auto;
        background-color:var(--jp-layout-color1, #ffffff);
        color:var(--jp-content-font-color1, #000000);
        font-family:sans-serif;
        line-height:1.5;
    ">
        {html_content}
    </div>
    """

class SubBox(VBox):
    """
    SubBox with:
      - Title
      - Optional instructions
      - User-defined inputs
      - User-defined buttons + Back
      - README preview
      - Shared log (updates automatically across all subboxes)
    """

    def __init__(self, title: str,
                 inputs=None,
                 buttons=None,
                 readme_section=None,
                 readme_path="README.md",
                 instructions=None,  # <-- New instructions parameter
                 width="100%",
                 feedback=True):

        global GLOBAL_LOG_WIDGET

        if inputs is None:
            inputs = []
        if buttons is None:
            buttons = []

        # Title
        self.title = HTML(f"<b>{title}</b>")

        # Instructions in the middle
        self.instructions = HTML(f"<i>{instructions}</i>") if instructions else None

        # Feedback label
        self.feedback_label = Label() if feedback else None

        # Shared log output (all subboxes point to the same widget)
        if GLOBAL_LOG_WIDGET is None:
            GLOBAL_LOG_WIDGET = Textarea(
                value=GLOBAL_LOG,
                disabled=True,
                layout=Layout(width="95%", height="100px"),
                style={"font_family": "monospace"}
            )
        self.log_output = GLOBAL_LOG_WIDGET

        # Buttons row (user buttons)
        button_row = HBox(buttons,
                          layout=Layout(justify_content="flex-start", width="100%"))

        # Left column
        left_items = [self.title]
        if self.instructions:
            left_items.append(self.instructions)  # instructions appear after title
        left_items += inputs + [button_row, self.log_output]
        if feedback:
            left_items.append(self.feedback_label)
        left_col = VBox(left_items, layout=Layout(width="70%", gap="10px"))

        # Right column (README preview)
        if readme_section:
            readme_html = load_readme_section(readme_section, readme_path)
            right_col = VBox(
                [HTML(f"<b>README: {readme_section}</b>"), HTML(readme_html)],
                layout=Layout(width="30%", border="1px solid #ccc", padding="5px")
            )
        else:
            right_col = VBox([], layout=Layout(width="30%"))

        # Full box
        super().__init__([HBox([left_col, right_col], layout=Layout(width="100%"))],
                         layout=Layout(
                             border="1px solid #ccc",
                             padding="10px",
                             margin="5px 0",
                             width=width,
                             gap="10px"
                         ))

    # --- Logging function shared across all subboxes ---
    @staticmethod
    def log(message, list_mode=False):
        """
        Updates GLOBAL_LOG and refreshes the shared log widget in all subboxes.
        Supports list_mode.
        """
        global GLOBAL_LOG, GLOBAL_LOG_WIDGET
        if list_mode:
            if GLOBAL_LOG:
                GLOBAL_LOG = f"{message}, " + GLOBAL_LOG
            else:
                GLOBAL_LOG = message
        else:
            if GLOBAL_LOG:
                GLOBAL_LOG = f"{message}\n" + GLOBAL_LOG
            else:
                GLOBAL_LOG = message
        if GLOBAL_LOG_WIDGET is not None:
            GLOBAL_LOG_WIDGET.value = GLOBAL_LOG

    # --- Clear log function ---
    @staticmethod
    def clear_log():
        """
        Clears the shared global log and updates all subboxes.
         """
        global GLOBAL_LOG, GLOBAL_LOG_WIDGET
        GLOBAL_LOG = ""
        if GLOBAL_LOG_WIDGET is not None:
            GLOBAL_LOG_WIDGET.value = ""