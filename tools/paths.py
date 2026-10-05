"""Every machine-specific path in one place. Override any of them with the environment variable of the same name.

GAME         GHWT:DE install (GHWT_Definitive.exe).
GAME_CONFIG  the DE's settings folder (GHWTDE.ini).
GH_TOOLS     Guitar Hero SDK checkout (node: guitar-hero-sdk/sdk.js, png2img.js) + x360img.py / x360tex.py.
WOR_EXTRACT  textures, fonts and descs extracted from your own Warriors of Rock copy (x360img PNGs).
DE_EXTRACT   decompiled DE / World Tour+ / GH3:WoR material (scripts, GH3:WoR multiplier and light images).
GH5_VIDEO    GH5 reference footage (original.mp4) used by the mocks.

Game assets are never committed: the build reads them from these folders and packs them into the mod."""
import os

_DEFAULTS = {
    'GAME': r'D:\Games\Guitar Hero World Tour',
    'GAME_CONFIG': r'C:\Users\rockb\OneDrive\Documentos\My Games\Guitar Hero World Tour Definitive Edition',
    'GH_TOOLS': r'E:\Dev\ghwt\tools',
    'WOR_EXTRACT': r'E:\Dev\ghwt\ghwor-extract',
    'DE_EXTRACT': r'E:\Dev\ghwt\ghwt-extract',
    'GH5_VIDEO': r'E:\Dev\ghwt\reference-video',
}
GAME, GAME_CONFIG, GH_TOOLS, WOR_EXTRACT, DE_EXTRACT, GH5_VIDEO = (os.environ.get(k, v) for k, v in _DEFAULTS.items())

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
