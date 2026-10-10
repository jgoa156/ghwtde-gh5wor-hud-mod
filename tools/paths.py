"""Every machine-specific path in one place. Override any of them with the environment variable of the same name.

GAME         GHWT:DE install (GHWT_Definitive.exe).
GAME_CONFIG  the DE's settings folder (GHWTDE.ini).
GH_TOOLS     Guitar Hero SDK checkout (node: guitar-hero-sdk/sdk.js, png2img.js) + x360img.py / x360tex.py.
WOR_EXTRACT  textures, fonts and descs extracted from your own Warriors of Rock copy (x360img PNGs).
MENU_MUSIC_SOURCES  other DE menu music mods to merge into the menu music collection (kept OUT of DATA/MODS: the DE
             loads only one menu music mod).
WOR_XBOX     your own Warriors of Rock copy as pulled from the Xbox 360 (tools/xbox_pull.py; holds data/compressed).
DE_EXTRACT   decompiled DE / World Tour+ / GH3:WoR material (scripts, GH3:WoR multiplier and light images).
GH5_VIDEO    GH5 reference footage (original.mp4) used by the mocks.
RESHADE      folder with ReShade 6.8.0's 32-bit d3d9.dll (shipped in the package).
ASI_LOADER   Ultimate ASI Loader v9.7.4 x86 dinput8.dll (shipped in the package).

Game assets are never committed: the build reads them from these folders and packs them into the mod."""
import os

_DEFAULTS = {
    'GAME': r'D:\Games\Guitar Hero World Tour',
    'GAME_CONFIG': r'C:\Users\rockb\OneDrive\Documentos\My Games\Guitar Hero World Tour Definitive Edition',
    'GH_TOOLS': r'E:\Dev\ghwt\tools',
    'WOR_EXTRACT': r'E:\Dev\ghwt\ghwor-extract',
    'WOR_XBOX': r'E:\Guitar Hero - Warriors of Rock',
    'MENU_MUSIC_SOURCES': r'E:\Dev\ghwt\menu-music-sources',
    'DE_EXTRACT': r'E:\Dev\ghwt\ghwt-extract',
    'GH5_VIDEO': r'E:\Dev\ghwt\reference-video',
    'RESHADE': r'E:\Dev\ghwt\reshade-6.8.0',
    'ASI_LOADER': r'E:\Dev\ghwt\asi-loader-9.7.4\dinput8.dll',
}
GAME, GAME_CONFIG, GH_TOOLS, WOR_EXTRACT, WOR_XBOX, MENU_MUSIC_SOURCES, DE_EXTRACT, GH5_VIDEO, RESHADE, ASI_LOADER = (os.environ.get(k, v) for k, v in _DEFAULTS.items())

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SDK = os.path.join(GH_TOOLS, 'guitar-hero-sdk', 'sdk.js')
WOR_PNG = os.path.join(WOR_EXTRACT, 'z_in_game_png2')         # WoR z_in_game HUD textures
WOR_UI_PNG = os.path.join(WOR_EXTRACT, 'ui_shared_png2')       # WoR ui_shared textures
GH3WOR_PNG = os.path.join(DE_EXTRACT, 'gh3wor', 'global_png')  # GH3:WoR (DE mod) multiplier + streak light images


def wor(*parts):
    """A file under WOR_EXTRACT."""
    return os.path.join(WOR_EXTRACT, *parts)


def de(*parts):
    """A file under DE_EXTRACT."""
    return os.path.join(DE_EXTRACT, *parts)
