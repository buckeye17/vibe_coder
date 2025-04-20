import json
import os

import dash_mantine_components as dmc
from dash_iconify import DashIconify
import dash
from dash import Dash, _dash_renderer, Input, Output, State, callback, clientside_callback

from utils import get_directory_tree, read_file_safely, build_super_prompt

_dash_renderer._set_react_version("18.2.0")

app = Dash(external_stylesheets=dmc.styles.ALL)

theme_toggle = dmc.Switch(
    offLabel=DashIconify(
        icon="radix-icons:sun", width=15, color=dmc.DEFAULT_THEME["colors"]["yellow"][8]
    ),
    onLabel=DashIconify(
        icon="radix-icons:moon",
        width=15,
        color=dmc.DEFAULT_THEME["colors"]["yellow"][6],
    ),
    id="color-scheme-toggle",
    persistence=True,
    color="grey",
)

settings = [
    dmc.NumberInput(
        value=2,
        min=0,
        label="Tree Max Depth",
        description="Prevents file tree build out from getting crazy",
        id="tree-depth"
    ),

    dmc.NumberInput(
        value=50,
        min=1,
        label="Abort Super Prompt Threshold",
        description="Building the super prompt will be aborted if there are more than this many files",
        id="n-files-abort"
    ),

    dmc.TagsInput(
        value=["assets", "secret"],
        label="Sub-directories to Ignore",
        placeholder="path/to/excluded/dir",
        id="ignore-dirs",
    ),

    dmc.TagsInput(
        label="File Extensions to Ignore",
        placeholder="json",
        id="ignore-exts",
    ),
]

body = dmc.Grid([
    dmc.GridCol([
        dmc.Accordion([
            dmc.AccordionItem([
                dmc.AccordionControl("Settings"),
                dmc.AccordionPanel(settings)
            ],
            value="settings"),
        ]),
        
        dmc.TextInput(
            placeholder="/path/to/project",
            label="Base Folder",
            description="The root folder for the file tree explorer",
            id="base-folder"
        ),

        dmc.InputWrapper(
            dmc.Tree(
                data=[],
                checkboxes=True,
                expandedIcon=DashIconify(icon="fa6-regular:folder-open"),
                collapsedIcon=DashIconify(icon="fa6-solid:folder-plus"),
                id="file-tree"
            ),
            label="File Tree",
            description="Pick the files to be included in super prompt"
        )


    ], span=3),
    dmc.GridCol(
        dmc.Stack([
            dmc.Textarea(
                label="Prompt",
                placeholder='“Why would you reorder from a computer when '
                'you can have the personal touch of a salesman?" - '
                'Dwight, Assistant to the Regional Manager',
                autosize=True,
                minRows=2,
                maxRows=4,
                id="prompt",
            ),
            dmc.InputWrapper(
                dmc.CodeHighlight(
                    code="",
                    language="markdown",
                    style={"withExpandButton": True, "defaultExpanded": False},
                    id="super-prompt"
                ),
                label="Super Prompt",
                description="This is the entire prompt you'll paste into the LLM chat",
            )
        ]),
        span=9
    )
])

layout = dmc.AppShell(
    [
        dmc.AppShellHeader(
            dmc.Group(
                [
                    dmc.Group(
                        [
                            DashIconify(
                                icon="flowbite:laptop-code-outline",
                                color=dmc.DEFAULT_THEME["colors"]["blue"][5],
                                width=40,
                            ),
                            dmc.Title("Assistant to the Vibe Coder", c="blue"),
                        ]
                    ),
                    theme_toggle,
                ],
                justify="space-between",
                style={"flex": 1},
                h="100%",
                px="md",
            ),
        ),
        dmc.AppShellMain(body),
    ],
    header={"height": 60},
    padding="md",
    id="appshell",
)

app.layout = dmc.MantineProvider(layout)


@callback(
    Output("base-folder", "error"),
    Output("file-tree", "data"),
    Input("base-folder", "value"),
    Input("tree-depth", "value"),
    Input("ignore-dirs", "value"),
    Input("ignore-exts", "value"),
)
def update_file_tree(dir, depth, ignore_dirs, ignore_exts):
    if isinstance(dir, str) and isinstance(depth, int) and os.path.exists(dir):
        return False, get_directory_tree(dir, depth, ignore_dirs, ignore_exts)
    elif isinstance(dir, str) and os.path.exists(dir):
        return False, []
    return True, []


@callback(
    Output("super-prompt", "code"),
    Input("file-tree", "checked"),
    Input("prompt", "value"),
    State("base-folder", "value"),
    State("n-files-abort", "value"),
)
def update_super_prompt(files, prompt, base_dir, abort_threshold):
    if not files or not base_dir:
        return ""
    
    return build_super_prompt(files, base_dir, prompt, abort_threshold)


clientside_callback(
    """ 
    (switchOn) => {
       document.documentElement.setAttribute('data-mantine-color-scheme', switchOn ? 'dark' : 'light');  
       return window.dash_clientside.no_update
    }
    """,
    Output("color-scheme-toggle", "id"),
    Input("color-scheme-toggle", "checked"),
)

if __name__ == "__main__":
    app.run(debug=False)
