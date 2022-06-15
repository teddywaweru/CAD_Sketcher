import bpy
from bpy.types import Panel, Menu, UIList
from . import operators, functions, class_defines

"""
DEFAULT ON COMMENTING:

'C' is used to reference Blender's 'bpy.context'/'bpy.data' Class Instances
"""


#Instance of UIlist for drawing list of sketches in active scene.
class VIEW3D_UL_sketches(UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index=0
    ):
        """Function draws each sketch(item) in the add-on's Sketcher Panel

        Args:
            context (_type_): _description_
            layout (_type_): _description_
            data (C.scene.sketcher.entities): _description_
            item (C.scene.sketcher.entities.sketches): _description_
            icon (_type_): _description_
            active_data (C.scenes['Scene'].sketcher): _description_
            active_propname (_type_): _description_
            index (int, optional): _description_. Defaults to 0.
        """
        #A00 is the draw_item function call called iteratively for each item in the collection?

        #A00 where is the declaration of the layout_type? Does it mean 
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            if item:
                active = index == getattr(active_data, active_propname)

                row = layout.row(align=True)
                row.alignment = "LEFT"

                #Property Object to toggle visibility of sketch
                row.prop(
                    item,
                    "visible",
                    icon_only=True,
                    icon=("HIDE_OFF" if item.visible else "HIDE_ON"),
                    emboss=False,
                )

                #Property Object to display Sketch name 
                row.prop(item, "name", text="", emboss=False, icon_value=icon)

                row = layout.row()
                row.alignment = "RIGHT"

                #If state of sketch solver is not okay, display error icon
                #A00 what part of code shows actual error in pop up? & symbol?
                if item.solver_state != "OKAY":
                    row.operator(
                        operators.View3D_OT_slvs_show_solver_state.bl_idname,
                        text="",
                        emboss=False,
                        icon_value=layout.enum_item_icon(
                            item, "solver_state", item.solver_state
                        ),
                    ).index = item.slvs_index

                #Display edit button & connected to Enable Active Sketch Operator
                row.operator(
                    operators.View3D_OT_slvs_set_active_sketch.bl_idname,
                    icon="OUTLINER_DATA_GP_LAYER",
                    text="",
                    emboss=False,
                ).index = item.slvs_index

                # For active sketch, display the Delete button
                if active:
                    row.operator(
                        operators.View3D_OT_slvs_delete_entity.bl_idname,
                        text="",
                        icon="X",
                        emboss=False,
                    ).index = item.slvs_index
                else:
                    row.separator()
                    row.separator()

            else:
                layout.label(text="", translate=False, icon_value=icon)
        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text="", icon_value=icon)


class VIEW3D_PT_sketcher(Panel):
    bl_label = "Sketcher"
    bl_idname = "VIEW3D_PT_sketcher"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Sketcher"

    def draw(self, context):
        layout = self.layout

        sketch_selector(context, layout, show_selector=False)
        sketch = context.scene.sketcher.active_sketch
        layout.use_property_split = True
        layout.use_property_decorate = False

        if sketch:
            row = layout.row()
            row.alignment = "CENTER"
            row.scale_y = 1.2

            if sketch.solver_state != "OKAY":
                state = sketch.get_solver_state()
                row.operator(
                    operators.View3D_OT_slvs_show_solver_state.bl_idname,
                    text=state.name,
                    icon=state.icon,
                    emboss=False,
                ).index = sketch.slvs_index
            else:
                dof = sketch.dof
                dof_ok = dof <= 0
                dof_msg = "Fully defined sketch" if dof_ok else "Degrees of freedom: " + str(dof)
                dof_icon = "CHECKMARK" if dof_ok else "ERROR"
                row.label(text=dof_msg, icon=dof_icon)

            layout.separator()

            row = layout.row()
            row.prop(sketch, "name")
            layout.prop(sketch, "convert_type")
            if sketch.convert_type != "NONE":
                layout.prop(sketch, "fill_shape")

            layout.operator(
                operators.View3D_OT_slvs_delete_entity.bl_idname,
                text="Delete Sketch",
                icon="X",
            ).index = sketch.slvs_index

        else:
            layout.template_list(
                "VIEW3D_UL_sketches",
                "",
                context.scene.sketcher.entities,
                "sketches",
                context.scene.sketcher,
                "ui_active_sketch",
            )

        layout.separator()

        layout.label(text="Constraints:")
        col = layout.column(align=True)
        for op in operators.constraint_operators:
            col.operator(op.bl_idname)

        prefs = functions.get_prefs()
        if prefs.show_debug_settings:
            layout.use_property_split = False
            layout.separator()
            layout.label(text="Debug:")
            layout.label(text="Version: " + str(context.scene.sketcher.version[:]))

            layout.operator(operators.VIEW3D_OT_slvs_write_selection_texture.bl_idname)
            layout.operator(operators.View3D_OT_slvs_solve.bl_idname)
            layout.operator(
                operators.View3D_OT_slvs_solve.bl_idname, text="Solve All"
            ).all = True

            layout.operator(operators.View3D_OT_slvs_test.bl_idname)
            layout.prop(context.scene.sketcher, "show_origin")
            layout.prop(prefs, "hide_inactive_constraints")
            layout.prop(prefs, "all_entities_selectable")
            layout.prop(prefs, "force_redraw")


class VIEW3D_PT_sketcher_entities(Panel):
    bl_label = "Entities"
    bl_idname = "VIEW3D_PT_sketcher_entities"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Sketcher"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        col = box.column(align=True)
        col.scale_y = 0.8

        sketch = context.scene.sketcher.active_sketch
        for e in context.scene.sketcher.entities.all:
            if not e.is_active(sketch):
                continue
            if isinstance(e, class_defines.SlvsSketch):
                continue

            row = col.row()
            row.alert = e.selected

            # Left part
            sub = row.row()
            sub.alignment = "LEFT"

            # Visibility toggle
            sub.prop(
                e,
                "visible",
                icon_only=True,
                icon=("HIDE_OFF" if e.visible else "HIDE_ON"),
                emboss=False,
            )

            # Select operator
            props = sub.operator(
                operators.View3D_OT_slvs_select.bl_idname,
                text=str(e),
                emboss=False
                )
            props.index = e.slvs_index
            props.highlight_hover = True


            # Right part
            sub = row.row()
            sub.alignment = "RIGHT"

            # Context menu
            props = sub.operator(
                operators.View3D_OT_slvs_context_menu.bl_idname,
                text="",
                icon="OUTLINER_DATA_GP_LAYER",
                emboss=False
                )
            props.highlight_hover = True
            props.highlight_active = True
            props.index = e.slvs_index

            # Delete operator
            props = sub.operator(
                operators.View3D_OT_slvs_delete_entity.bl_idname,
                text="",
                icon="X",
                emboss=False
                )
            props.index = e.slvs_index
            props.highlight_hover = True


class VIEW3D_PT_sketcher_constraints(Panel):
    bl_label = "Constraints"
    bl_idname = "VIEW3D_PT_sketcher_constraints"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Sketcher"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        col = box.column(align=True)
        col.scale_y = 0.8

        sketch = context.scene.sketcher.active_sketch
        for c in context.scene.sketcher.constraints.all:
            if not c.is_active(sketch):
                continue
            row = col.row()

            # Left part
            sub = row.row()
            sub.alignment = "LEFT"

            # Failed hint
            sub.label(
                text="",
                icon=("ERROR" if c.failed else "CHECKMARK"),
            )

            index = context.scene.sketcher.constraints.get_index(c)

            # Context menu, shows constraint name
            props = sub.operator(
                operators.View3D_OT_slvs_context_menu.bl_idname,
                text=str(c),
                emboss=False
                )
            props.type = c.type
            props.index = index
            props.highlight_hover = True
            props.highlight_active = True

            # Right part
            sub = row.row()
            sub.alignment = "RIGHT"

            # Delete operator
            props = sub.operator(
                operators.View3D_OT_slvs_delete_constraint.bl_idname,
                text="",
                icon="X",
                emboss=False
            )
            props.type = c.type
            props.index = index
            props.highlight_hover = True


class VIEW3D_MT_sketches(Menu):
    bl_label = "Sketches"
    bl_idname = "VIEW3D_MT_sketches"

    def draw(self, context):
        layout = self.layout
        sse = context.scene.sketcher.entities
        layout.operator(
            operators.View3D_OT_slvs_add_sketch.bl_idname
        ).wait_for_input = True

        if len(sse.sketches):
            layout.separator()

        for i, sk in enumerate(sse.sketches):
            layout.operator(
                operators.View3D_OT_slvs_set_active_sketch.bl_idname, text=sk.name
            ).index = sk.slvs_index


class VIEW3D_PT_sketcher_attributes(Panel):
    bl_label = "Attributes"
    bl_idname = "VIEW3D_PT_sketcher_attributes"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Sketcher"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self,context):
        layout = self.layout

        row = layout.row()


#Create Pie Menu object
class CS_MT_Bool_Menu(Menu):
    bl_idname = "CS_MT_Bool_Menu"
    bl_label = "Pie Menu"

    def draw(self,context):
        layout = self.layout

        pie = layout.menu_pie()

        active_object = context.active_object

        if active_object:
            mode= active_object.mode

            if mode=="OBJECT":
                pie.operator(operators.View3D_OT_slvs_set_active_sketch.bl_idname,
                            icon="MOD_BOOLEAN")


def sketch_selector(context, layout, is_header=False, show_selector=True):
    row = layout.row(align=is_header)
    index = context.scene.sketcher.active_sketch_i
    name = "Sketches"

    scale_y = 1 if is_header else 1.8

    if index != -1:
        sketch = context.scene.sketcher.active_sketch
        name = sketch.name

        row.operator(
            operators.View3D_OT_slvs_set_active_sketch.bl_idname,
            text="Leave: " + name,
            icon="BACK",
            depress=True,
        ).index = -1

        row.active = True
        row.scale_y = scale_y

    else:
        row.scale_y = scale_y
        # TODO: Don't show text when is_header
        #A00 why not show text here? else show from where?
        row.operator(
            operators.View3D_OT_slvs_add_sketch.bl_idname, icon="ADD"
        ).wait_for_input = True

        if not is_header:
            row = layout.row()
        if show_selector:
            row.menu(VIEW3D_MT_sketches.bl_idname, text=name)

def draw_object_context_menu(self, context):
    layout = self.layout
    ob = context.active_object
    row = layout.row()

    props = row.operator(operators.View3D_OT_slvs_set_active_sketch.bl_idname, text="Edit Sketch")

    if ob and ob.sketch_index != -1:
        row.active = True
        props.index = ob.sketch_index
    else:
        row.active = False
    layout.separator()


        

classes = (
    VIEW3D_UL_sketches,
    VIEW3D_PT_sketcher,
    VIEW3D_PT_sketcher_entities,
    VIEW3D_PT_sketcher_constraints,
    VIEW3D_PT_sketcher_attributes,
    VIEW3D_MT_sketches,
    CS_MT_Bool_Menu
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    kc = bpy.context.window_manager.keyconfigs.addon
    km = kc.keymaps.new(name="3D View", space_type="VIEW_3D")

    km_menu = km.keymap_items.new("wm.call_menu_pie","COMMA","PRESS", shift=True)
    km_menu.properties.name = CS_MT_Bool_Menu.bl_idname

    bpy.types.VIEW3D_MT_object_context_menu.prepend(draw_object_context_menu)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    bpy.types.VIEW3D_MT_object_context_menu.remove(draw_object_context_menu)
