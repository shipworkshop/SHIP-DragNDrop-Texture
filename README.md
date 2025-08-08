
# Smart Texture Drag & Drop for Blender

![Blender](https://img.shields.io/badge/Blender-4.1+-orange.svg)

A simple yet powerful Blender addon that streamlines the material creation process. Just drag and drop a texture onto an object, and the addon will automatically find and connect the entire PBR texture set.

**(Recommended: Record a short GIF showing the drag-and-drop workflow and replace the link below.)**
![Smart Drag & Drop Demo]![T2ScVsLiCn](https://github.com/user-attachments/assets/0caf601d-15e7-44b5-ba72-50f9d63c02f0)


## Key Features

*   **Drag & Drop Workflow:** Simply drag a texture file from your explorer onto any object in the 3D Viewport.
*   **Automatic PBR Set Detection:** Intelligently finds and connects maps for Base Color, Metallic, Roughness, and Normals based on filename suffixes.
*   **Two Modes of Operation:**
    1.  **Smart Apply (Default):** Finds and applies the entire texture set automatically.
    2.  **Manual Apply:** Applies only the single dragged texture to a specific input of your choice.
*   **Interactive Control:** Immediately after dropping a texture, press `F9` to open the "Redo Last" panel and switch between modes or change settings.
*   **Intelligent Socket Guessing:** If you drop a file named `MyTexture_normal.png` in manual mode, the addon will correctly default to the "Normal" socket.

## How It Works

The addon's "Smart Apply" feature works by identifying a **base name** from the file you drop and searching for common PBR suffixes.

**Example:** If you drop `Wood_Planks_Normal.png`, the base name is `Wood_Planks`. The addon will then search the same directory for other files like:
*   `Wood_Planks_Color.png`
*   `Wood_Planks_Roughness.png`
*   `Wood_Planks_Metallic.png`

#### Supported Suffixes:
*   **Color:** `_color`, `_albedo`, `_diffuse`, `_basecolor`, `_col`
*   **Metallic:** `_metallic`, `_metal`, `_metalnessmask`
*   **Roughness:** `_roughness`, `_rough`
*   **Normal:** `_normal`, `_nrm`, `_normalgl`

## Installation

1.  Go to the [**Releases**](https://github.com/YOUR_USERNAME/YOUR_REPOSITORY/releases) page.
2.  Download the latest `smart_texture_drop.zip` file.
3.  In Blender, go to `Edit` > `Preferences` > `Add-ons`.
4.  Click `Install...` and select the downloaded `.zip` file.
5.  Enable the "Smart Drag & Drop" addon by checking the box.

## Usage

1.  Drag any texture file from your file browser directly onto an object in the 3D Viewport.
2.  The material is instantly created or updated.
3.  **Immediately after**, press `F9` (or open the "Redo Last" panel at the bottom-left of the viewport) to change the settings:
    *   **`Smart Apply`** (checked by default): Looks for all related textures in the folder.
    *   Uncheck it for **Manual Mode** to only apply the single texture you dropped.
    *   **`Target Socket`**: If in Manual Mode, choose which input to connect the texture to.
