"""Common PDF figure export. No global font installation or research-root dependency."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
from matplotlib import font_manager, rcParams
from matplotlib.text import Text

_font_faces = {}

def find_package_root(start):
    start = Path(start).resolve()
    for candidate in (start, *start.parents):
        if (candidate / 'config/workspace.json').is_file():
            return candidate
    raise FileNotFoundError('No package metadata found above starting directory')

def configure_fonts(font_dir):
    global _font_faces
    font_dir = Path(font_dir)
    _font_faces = {name: font_dir / filename for name, filename in {
        'regular':'STIXTwoText-Regular.ttf', 'italic':'STIXTwoText-Italic.ttf',
        'medium':'STIXTwoText-Medium.ttf', 'medium_italic':'STIXTwoText-MediumItalic.ttf'}.items()}
    for font in _font_faces.values():
        font_manager.fontManager.addfont(str(font))
    rcParams.update({'font.family':'STIX Two Text','font.size':9,
        'axes.labelsize':10,'axes.titlesize':11,'axes.titleweight':'medium','xtick.labelsize':9,
        'ytick.labelsize':9,'legend.fontsize':9,'pdf.fonttype':42,
        'ps.fonttype':42,'figure.facecolor':'white','axes.facecolor':'white'})

def save_pdf(fig, destination, width_mm=156, height_mm=110):
    destination=Path(destination)
    if destination.suffix.lower()!='.pdf':
        raise ValueError('Manuscript plot exports must be PDF')
    destination.parent.mkdir(parents=True,exist_ok=True)
    fig.set_size_inches(width_mm/25.4,height_mm/25.4)
    # Resolve faces explicitly so system fonts cannot reintroduce Bold or another release.
    for label in fig.findobj(Text):
        props = label.get_fontproperties().copy()
        weight = props.get_weight()
        numeric_weight = font_manager.weight_dict.get(weight, 400) if isinstance(weight, str) else weight
        face = 'medium' if numeric_weight >= 500 else 'regular'
        if props.get_style() in ('italic', 'oblique'):
            face = 'italic' if face == 'regular' else face + '_italic'
        props.set_file(str(_font_faces[face]))
        if numeric_weight >= 500:
            props.set_weight(500)
        label.set_fontproperties(props)
    fig.savefig(destination,format='pdf',facecolor='white')
    return destination
