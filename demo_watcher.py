# %%
from build123d import *
from ocp_vscode import *

set_port(3939)
set_defaults(ortho=True, default_edgecolor="#121212", reset_camera=Camera.KEEP, axes=True, axes0=True)

length, width, thickness = 80.0, 60.0, 80.0

with BuildPart() as ex16_single:
    with BuildSketch(Plane.XZ) as ex16_sk:
        Rectangle(length, width)
        fillet(ex16_sk.vertices(), radius=length / 10)
        with GridLocations(x_spacing=length / 4, y_spacing=0, x_count=3, y_count=1):
            Circle(length / 12, mode=Mode.SUBTRACT)
        Rectangle(length, width, align=(Align.MIN, Align.MIN), mode=Mode.SUBTRACT)
    extrude(amount=thickness)

with BuildPart() as ex16:
    add(ex16_single.part)
    mirror(ex16_single.part, about=Plane.XY.offset(width))
    mirror(ex16_single.part, about=Plane.YX.offset(width))
    mirror(ex16_single.part, about=Plane.YZ.offset(width))
    mirror(ex16_single.part, about=Plane.YZ.offset(-width))  

set_colormap(ColorMap.seeded(colormap="rgb", alpha=1, seed_value="vscod"))
# fmt: off
show_all(
    classes = [BuildPart, BuildSketch, BuildLine, ],  # comment to show all objects
    include = ["", ],
    exclude = ["", ],
    show_sketch_local = False,
    helper_scale = 1,  # controls size of e.g. planes and axes
)  # fmt: on
