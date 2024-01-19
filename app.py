from urllib.parse import parse_qs

import os
import requests
import dash
from dash import html
from dash import dcc
from dash.dependencies import Input, Output

from pymatgen.core import Structure
import crystal_toolkit.components as ctc
from crystal_toolkit.settings import SETTINGS

from flask_caching import Cache


app = dash.Dash(
    assets_folder=SETTINGS.ASSETS_PATH,
    requests_pathname_prefix="/crystal/viewer/",
    routes_pathname_prefix="/crystal/viewer/",
    serve_locally=True,
    title="Crystal Viewer",
    update_title=None,
    compress=True,
)

if os.environ.get("REDIS_URL"):
    cache = Cache(
        app.server,
        config={
            "CACHE_TYPE": "redis",
            "CACHE_REDIS_URL": os.environ.get("REDIS_URL", "localhost:6379"),
            "CACHE_DEFAULT_TIMEOUT": 60 * 60 * 24 * 30,
        },
    )
else:
    cache = None

structure_component = ctc.StructureMoleculeComponent(id="main_structure")
layout = structure_component.layout()
layout.style = {"width": "100%", "height": "100%"}
layout = html.Div([layout])
if cache:
    ctc.register_crystal_toolkit(app, layout, cache=cache)
else:
    ctc.register_crystal_toolkit(app, layout)

app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),
        dash.dcc.Loading(
            id="loading",
            type="default",
            children=html.Div(id="loading-output"),
            style={"height": "100%", "zIndex": 1000},
        ),
        app.layout,
        html.Script(id="scripts"),
    ]
)


app.clientside_callback(
    """
    function(search) {
      var fullscreenBtn = document.querySelector(".mpc-button-bar button");
      var CTmainStructureScene = document.querySelector('#CTmain_structure_scene');

      function isActive(){
         return document.querySelector('#CTmain_structure_scene.is-active') != undefined
      }

      fullscreenBtn.addEventListener('click', function(event) {
        event.preventDefault();
        if (!isActive()) {
            var requestFullScreen = CTmainStructureScene.requestFullscreen || CTmainStructureScene.webkitRequestFullscreen || CTmainStructureScene.mozRequestFullScreen || CTmainStructureScene.msRequestFullscreen;
            if (requestFullScreen) {
                requestFullScreen.call(CTmainStructureScene);
            }
        } else {
            exitFullscreen();
        }
      });

      function exitFullscreen() {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        } else if (document.mozCancelFullScreen) { // Firefox
            document.mozCancelFullScreen();
        } else if (document.webkitExitFullscreen) { // Chrome, Safari, and Opera
            document.webkitExitFullscreen();
        } else if (document.msExitFullscreen) { // IE/Edge
            document.msExitFullscreen();
        }
      }
    }
    """,
    Output("scripts", "children"),
    [Input("url", "search")],
)


@app.callback(
    [Output(structure_component.id(), "data"), Output("loading-output", "children")],
    [Input("url", "search")],
)
def display_page(search):
    qs = parse_qs(search.lstrip("?"))
    su = qs.get("structure-url")
    sf = qs.get("structure-format")
    sp = qs.get("supercell")
    if (not su) or (not sf):
        return None, None
    structure_url = su[0]
    structure_format = sf[0]
    response = requests.get(structure_url)
    response.raise_for_status()
    structure = Structure.from_str(response.text, structure_format)
    if sp:
        x, y, z = sp[0].split(",")
        structure.make_supercell(
            scaling_matrix=[int(x), int(y), int(z)], to_unit_cell=False
        )
    return structure, None


server = app.server


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=50002)
