bl_info = {
    "name": "Smart Drag & Drop Texture Set",
    "author": "Yurii Konoplov, Gemini",
    "version": (1, 1, 0),  # Version updated for localization
    "blender": (4, 1, 0),
    "location": "3D Viewport & F9 Panel",
    "description": "Drag and drop a texture onto an object. The addon will automatically find the texture set (Normal, Roughness, etc.) or allow you to manually assign a single texture via the F9 panel.",
    "warning": "For automatic mode, texture names should follow the 'Name_Suffix.ext' format.",
    "doc_url": "https://github.com/shipworkshop/SHIP-DragNDrop-Texture", 
    "category": "Material",
}

import bpy
import os
from bpy_extras.view3d_utils import region_2d_to_vector_3d, region_2d_to_origin_3d

IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tga')

SUFFIX_MAP = {
    "_normal": "Normal", "_nrm": "Normal", "_normalgl": "Normal",
    "_metallic": "Metallic", "_metal": "Metallic", "_metalnessmask": "Metallic",
    "_roughness": "Roughness", "_rough": "Roughness",
}
BASE_COLOR_SUFFIXES = ["_color", "_albedo", "_diffuse", "_basecolor", "_col"]

def guess_socket_from_filename(filename):
    """Analyzes the filename and guesses the most likely socket."""
    filename_no_ext, _ = os.path.splitext(filename)
    test_name = filename_no_ext.lower()

    # Sort by length to check for '_metalnessmask' before '_metal'
    for suffix, socket_name in sorted(SUFFIX_MAP.items(), key=lambda item: len(item[0]), reverse=True):
        if test_name.endswith(suffix):
            return socket_name

    for suffix in sorted(BASE_COLOR_SUFFIXES, key=len, reverse=True):
        if test_name.endswith(suffix):
            return "Base Color"
    
    return "Base Color"

def find_texture_set(directory, dropped_filename):
    """Finds the texture set and the base name."""
    # 1. Determine the base name by stripping known suffixes
    base_name = ""
    filename_no_ext, _ = os.path.splitext(dropped_filename)
    test_name = filename_no_ext.lower()
    
    all_suffixes = sorted(list(SUFFIX_MAP.keys()) + BASE_COLOR_SUFFIXES, key=len, reverse=True)
    found_suffix = False
    for suffix in all_suffixes:
        if test_name.endswith(suffix):
            base_name = filename_no_ext[:-len(suffix)]
            found_suffix = True
            break
    if not found_suffix:
        base_name = filename_no_ext

    # 2. Scan the folder neutrally, looking for all matching files
    texture_set = {}
    fallback_base_color_path = None

    for filename in os.listdir(directory):
        if not filename.lower().startswith(base_name.lower()):
            continue

        f_name_no_ext, f_ext = os.path.splitext(filename)
        if f_ext.lower() not in IMAGE_EXTENSIONS:
            continue

        test_f_name = f_name_no_ext.lower()
        file_path = os.path.join(directory, filename)
        identified = False

        # Priority 1: Look for specific maps (Normal, Metallic, etc.)
        for suffix, socket_name in sorted(SUFFIX_MAP.items(), key=lambda item: len(item[0]), reverse=True):
            if test_f_name.endswith(suffix):
                if socket_name not in texture_set:
                    texture_set[socket_name] = file_path
                identified = True
                break
        if identified:
            continue

        # Priority 2: Look for explicit color maps
        for suffix in sorted(BASE_COLOR_SUFFIXES, key=len, reverse=True):
            if test_f_name.endswith(suffix):
                if "Base Color" not in texture_set:
                    texture_set["Base Color"] = file_path
                identified = True
                break
        if identified:
            continue

        # Priority 3: Look for a file without a suffix as a possible Base Color
        if test_f_name == base_name.lower():
            fallback_base_color_path = file_path

    # 3. Apply the file without a suffix as Base Color if an explicit one was not found
    if "Base Color" not in texture_set and fallback_base_color_path:
        texture_set["Base Color"] = fallback_base_color_path
        
    # 4. Ensure the dropped file is always in the set if it wasn't recognized
    dropped_path_full = os.path.join(directory, dropped_filename)
    if not any(os.path.normpath(p) == os.path.normpath(dropped_path_full) for p in texture_set.values()):
        socket = guess_socket_from_filename(dropped_filename)
        if socket not in texture_set:
            texture_set[socket] = dropped_path_full

    return texture_set, base_name


class OBJECT_OT_smart_texture_drop(bpy.types.Operator):
    """Applies textures to the object under the cursor, with options in the Redo Last panel."""
    bl_idname = "object.smart_texture_drop"
    bl_label = "Apply Texture"
    bl_options = {'REGISTER', 'UNDO'}

    files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement)
    directory: bpy.props.StringProperty(subtype="DIR_PATH")
    
    use_smart_apply: bpy.props.BoolProperty(
        name="Smart Apply",
        description="Automatically find and apply the texture set (Normal, Roughness, etc.)",
        default=True
    )
    
    target_socket: bpy.props.EnumProperty(
        name="Target Socket",
        description="Which socket to connect the single texture to (when 'Smart Apply' is disabled)",
        items=[
            ('Base Color', "Base Color", "Connect to the Base Color input"),
            ('Roughness', "Roughness", "Connect to the Roughness input"),
            ('Metallic', "Metallic", "Connect to the Metallic input"),
            ('Normal', "Normal", "Connect as a Normal Map")
        ],
        default='Base Color'
    )
    
    target_object_name: bpy.props.StringProperty()
    texture_set_str: bpy.props.StringProperty()
    base_name_str: bpy.props.StringProperty()

    def invoke(self, context, event):
        if not self.files: return {'CANCELLED'}
        
        depsgraph = context.evaluated_depsgraph_get()
        mouse_coords = (event.mouse_region_x, event.mouse_region_y)
        ray_origin = region_2d_to_origin_3d(context.region, context.space_data.region_3d, mouse_coords)
        ray_direction = region_2d_to_vector_3d(context.region, context.space_data.region_3d, mouse_coords)
        result, _, _, _, hit_object, _ = context.scene.ray_cast(depsgraph, ray_origin, ray_direction)
        
        if not (result and hit_object and hit_object.visible_get(view_layer=context.view_layer)):
            self.report({'INFO'}, "No visible object found under the cursor.")
            return {'CANCELLED'}

        context.view_layer.objects.active = hit_object
        hit_object.select_set(True)
        self.target_object_name = hit_object.name
        
        dropped_filename = self.files[0].name
        self.target_socket = guess_socket_from_filename(dropped_filename)
        
        texture_set, base_name = find_texture_set(self.directory, dropped_filename)
        self.texture_set_str = str(texture_set)
        self.base_name_str = base_name
        
        return self.execute(context)

    def execute(self, context):
        obj = bpy.data.objects.get(self.target_object_name)
        if not obj or obj.type not in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT'}:
            return {'CANCELLED'}

        texture_set = eval(self.texture_set_str)
        base_name = self.base_name_str
        
        target_mat = obj.active_material or (obj.data.materials[0] if obj.data.materials else None)
        if not target_mat:
            mat_name = base_name.replace("_", " ").replace("-", " ").strip() or "Material"
            target_mat = bpy.data.materials.new(name=mat_name.title())
            if obj.data.materials:
                 obj.data.materials[0] = target_mat
            else:
                 obj.data.materials.append(target_mat)
        
        target_mat.use_nodes = True
        nodes = target_mat.node_tree.nodes
        links = target_mat.node_tree.links
        bsdf = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if not bsdf:
            self.report({'ERROR'}, "Principled BSDF node not found in the material.")
            return {'CANCELLED'}
        
        if self.use_smart_apply:
            node_y_offset = 0
            # Sort for a more predictable node layout
            sorted_sockets = ["Base Color", "Metallic", "Roughness", "Normal"]
            for socket_name in sorted_sockets:
                if socket_name in texture_set:
                    filepath = texture_set[socket_name]
                    self._create_and_link_node(nodes, links, bsdf, socket_name, filepath, node_y_offset)
                    node_y_offset -= 300
            self.report({'INFO'}, f"Texture set '{base_name}' applied.")
        else:
            filepath = os.path.join(self.directory, self.files[0].name)
            self._create_and_link_node(nodes, links, bsdf, self.target_socket, filepath, 0)
            self.report({'INFO'}, f"Texture applied to the '{self.target_socket}' socket.")

        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "use_smart_apply")
        row = layout.row()
        row.enabled = not self.use_smart_apply
        row.prop(self, "target_socket")

    def _create_and_link_node(self, nodes, links, bsdf, socket_name, filepath, y_offset):
        try:
            img_node = nodes.new(type='ShaderNodeTexImage')
            img_node.image = bpy.data.images.load(filepath, check_existing=True)
            img_node.location = bsdf.location.x - 450, bsdf.location.y + y_offset
            
            if socket_name == "Base Color":
                img_node.image.colorspace_settings.name = 'sRGB'
                links.new(img_node.outputs['Color'], bsdf.inputs[socket_name])
            else:
                img_node.image.colorspace_settings.name = 'Non-Color'
                if socket_name == 'Normal':
                    normal_map_node = nodes.new(type='ShaderNodeNormalMap')
                    normal_map_node.location = img_node.location.x + 200, img_node.location.y
                    links.new(img_node.outputs['Color'], normal_map_node.inputs['Color'])
                    links.new(normal_map_node.outputs['Normal'], bsdf.inputs[socket_name])
                else: 
                    links.new(img_node.outputs['Color'], bsdf.inputs[socket_name])
        except Exception as e:
            self.report({'WARNING'}, f"Failed to process '{os.path.basename(filepath)}': {e}")


class OBJECT_FH_smart_texture_drop_handler(bpy.types.FileHandler):
    bl_idname = "OBJECT_FH_smart_texture_drop_handler"
    bl_label = "Smart Texture Drop Handler"
    bl_file_extensions = ";".join(IMAGE_EXTENSIONS)
    bl_import_operator = "object.smart_texture_drop"

    @classmethod
    def poll_drop(cls, context):
        return context.area and context.area.type == 'VIEW_3D'


classes = (
    OBJECT_OT_smart_texture_drop,
    OBJECT_FH_smart_texture_drop_handler,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
