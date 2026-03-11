"""
Motor de cálculo musical para generación de acordes.
Soporta instrumentos de 4 cuerdas con afinaciones personalizables.
"""

import re
from itertools import product
from typing import Optional

# Escala cromática (12 semitonos)
CHROMATIC_SCALE = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# Mapeo de notas con bemoles a sostenidos
ENHARMONIC_MAP = {
    'Db': 'C#', 'Eb': 'D#', 'Fb': 'E', 'Gb': 'F#',
    'Ab': 'G#', 'Bb': 'A#', 'Cb': 'B'
}

# Intervalos de acordes (semitonos desde la raíz)
# Formato: (intervalos, notas_requeridas_indices)
# notas_requeridas_indices indica qué posiciones del array de intervalos son obligatorias
CHORD_TYPES = {
    'Mayor': [0, 4, 7],
    'Menor': [0, 3, 7],
    '7ma': [0, 4, 7, 10],
    'Mayor 7': [0, 4, 7, 11],
    'Menor 7': [0, 3, 7, 10],
    'dim': [0, 3, 6],
    'aug': [0, 4, 8],
    'sus2': [0, 2, 7],
    'sus4': [0, 5, 7],
    'add9': [0, 4, 7, 14],
    '7sus4': [0, 5, 7, 10],
}

# Notas requeridas para cada tipo de acorde (índices de CHORD_TYPES[tipo])
# Por defecto: raíz (0) + característica (1) son requeridas
# Para acordes extendidos, se requiere también la extensión
REQUIRED_TONES = {
    'Mayor': [0, 1],        # Raíz + 3ra mayor
    'Menor': [0, 1],        # Raíz + 3ra menor
    '7ma': [0, 1, 3],       # Raíz + 3ra + 7ma
    'Mayor 7': [0, 1, 3],   # Raíz + 3ra + 7ma mayor
    'Menor 7': [0, 1, 3],   # Raíz + 3ra + 7ma
    'dim': [0, 1, 2],       # Raíz + 3ra menor + 5ta disminuida
    'aug': [0, 1, 2],       # Raíz + 3ra + 5ta aumentada
    'sus2': [0, 1],         # Raíz + 2da suspendida
    'sus4': [0, 1],         # Raíz + 4ta suspendida
    'add9': [0, 1, 3],      # Raíz + 3ra + 9na (la 9na es lo que lo hace add9)
    '7sus4': [0, 1, 3],     # Raíz + 4ta + 7ma
}

# Tipos básicos para búsqueda sin filtros
BASIC_CHORD_TYPES = ['Mayor', 'Menor']


def normalize_note_name(note: str) -> str:
    """Normaliza nombre de nota (convierte bemoles a sostenidos)."""
    if note in ENHARMONIC_MAP:
        return ENHARMONIC_MAP[note]
    return note


def parse_note(note_str: str) -> int:
    """
    Convierte una nota con octava a índice MIDI.
    Ejemplo: "C4" -> 60, "A#3" -> 58
    """
    match = re.match(r'^([A-Ga-g][#b]?)(\d+)$', note_str.strip())
    if not match:
        raise ValueError(f"Formato de nota inválido: {note_str}")
    
    note_name = match.group(1).upper()
    if len(note_name) == 2 and note_name[1] == 'B':
        note_name = note_name[0] + 'b'
    
    note_name = normalize_note_name(note_name)
    octave = int(match.group(2))
    
    if note_name not in CHROMATIC_SCALE:
        raise ValueError(f"Nota no reconocida: {note_name}")
    
    note_index = CHROMATIC_SCALE.index(note_name)
    midi_note = (octave + 1) * 12 + note_index
    return midi_note


def midi_to_note_name(midi_note: int) -> str:
    """Convierte índice MIDI a nombre de nota (sin octava)."""
    return CHROMATIC_SCALE[midi_note % 12]


def get_fret_note(open_string_midi: int, fret: int) -> int:
    """Calcula la nota MIDI en un traste específico."""
    return open_string_midi + fret


def is_playable(frets: tuple, max_stretch: int = 4) -> bool:
    """
    Verifica si una posición de acordes es anatómicamente ejecutable.
    La distancia entre el traste más bajo (>0) y el más alto no debe exceder max_stretch.
    """
    pressed = [f for f in frets if f > 0]
    if not pressed:
        return True
    return max(pressed) - min(pressed) <= max_stretch


def get_chord_notes(root: str, chord_type: str) -> set:
    """Obtiene el conjunto de notas que forman un acorde."""
    root_normalized = normalize_note_name(root)
    root_index = CHROMATIC_SCALE.index(root_normalized)
    intervals = CHORD_TYPES[chord_type]
    
    chord_notes = set()
    for interval in intervals:
        note_index = (root_index + interval) % 12
        chord_notes.add(CHROMATIC_SCALE[note_index])
    
    return chord_notes


def contains_required_tones(played_notes: list, root: str, chord_type: str) -> bool:
    """
    Verifica que las notas tocadas contengan todas las notas requeridas del acorde.
    Las notas requeridas varían según el tipo de acorde.
    """
    root_normalized = normalize_note_name(root)
    root_index = CHROMATIC_SCALE.index(root_normalized)
    intervals = CHORD_TYPES[chord_type]
    required_indices = REQUIRED_TONES.get(chord_type, [0, 1])
    
    played_note_names = set(played_notes)
    
    for req_idx in required_indices:
        interval = intervals[req_idx]
        note_index = (root_index + interval) % 12
        required_note = CHROMATIC_SCALE[note_index]
        if required_note not in played_note_names:
            return False
    
    return True


def matches_chord(played_notes: list, root: str, chord_type: str) -> bool:
    """
    Verifica si las notas tocadas forman el acorde especificado.
    Todas las notas tocadas deben pertenecer al acorde.
    """
    chord_notes = get_chord_notes(root, chord_type)
    played_set = set(played_notes)
    
    if not played_set.issubset(chord_notes):
        return False
    
    return contains_required_tones(played_notes, root, chord_type)


def find_chord_positions(
    tuning_midi: list,
    max_frets: int,
    root: str,
    chord_type: str,
    limit: int = 10,
    min_fret: int = 0,
    max_fret: Optional[int] = None,
    string_fret_filter: Optional[dict] = None
) -> list:
    """
    Encuentra posiciones válidas para un acorde específico.
    
    Args:
        tuning_midi: Lista de notas MIDI de la afinación
        max_frets: Número máximo de trastes del instrumento
        root: Nota raíz del acorde
        chord_type: Tipo de acorde
        limit: Máximo de posiciones a retornar
        min_fret: Traste mínimo del rango de búsqueda
        max_fret: Traste máximo del rango de búsqueda (None = max_frets)
        string_fret_filter: Diccionario {índice_cuerda: traste_requerido}
    """
    positions = []
    root_normalized = normalize_note_name(root)
    
    if max_fret is None:
        max_fret = max_frets
    
    # Crear rangos de trastes para cada cuerda
    fret_ranges = []
    for string_idx in range(4):
        if string_fret_filter and string_idx in string_fret_filter:
            # Si hay filtro para esta cuerda, solo ese traste
            fret_ranges.append([string_fret_filter[string_idx]])
        else:
            fret_ranges.append(range(min_fret, max_fret + 1))
    
    for frets in product(*fret_ranges):
        if not is_playable(frets):
            continue
        
        played_notes = []
        for i, fret in enumerate(frets):
            midi_note = get_fret_note(tuning_midi[i], fret)
            note_name = midi_to_note_name(midi_note)
            played_notes.append(note_name)
        
        if matches_chord(played_notes, root_normalized, chord_type):
            positions.append({
                'name': f"{root_normalized} {chord_type}",
                'root': root_normalized,
                'type': chord_type,
                'frets': list(frets),
                'notes': played_notes
            })
            
            if len(positions) >= limit:
                return positions
    
    return positions


def generate_chords(
    tuning: list,
    max_frets: int,
    root_filter: Optional[str] = None,
    type_filter: Optional[str] = None,
    limit: int = 10,
    min_fret: int = 0,
    max_fret: Optional[int] = None,
    string_fret_filter: Optional[dict] = None
) -> list:
    """
    Función principal para generar acordes.
    
    Args:
        tuning: Lista de notas de afinación ordenadas de grave a aguda
                [Cuerda4, Cuerda3, Cuerda2, Cuerda1] (ej: ["F3", "A#3", "D4", "G4"])
        max_frets: Número máximo de trastes del instrumento
        root_filter: Filtro de nota raíz (None = todas)
        type_filter: Filtro de tipo de acorde (None = Mayor y Menor)
        limit: Número máximo de resultados
        min_fret: Traste mínimo del rango de búsqueda
        max_fret: Traste máximo del rango de búsqueda (None = max_frets)
        string_fret_filter: Diccionario {índice_cuerda: traste_requerido}
                           donde índice 0=Cuerda4, 1=Cuerda3, 2=Cuerda2, 3=Cuerda1
    
    Returns:
        Lista de diccionarios con información de cada acorde encontrado.
        Los arrays 'frets' y 'notes' están en orden [Cuerda4, Cuerda3, Cuerda2, Cuerda1]
    """
    tuning_midi = [parse_note(note) for note in tuning]
    
    if root_filter:
        roots = [normalize_note_name(root_filter)]
    else:
        roots = CHROMATIC_SCALE.copy()
    
    if type_filter:
        chord_types = [type_filter]
    else:
        chord_types = BASIC_CHORD_TYPES
    
    all_positions = []
    
    for root in roots:
        for chord_type in chord_types:
            remaining = limit - len(all_positions)
            if remaining <= 0:
                break
            
            positions = find_chord_positions(
                tuning_midi,
                max_frets,
                root,
                chord_type,
                limit=remaining,
                min_fret=min_fret,
                max_fret=max_fret,
                string_fret_filter=string_fret_filter
            )
            all_positions.extend(positions)
            
            if len(all_positions) >= limit:
                break
        
        if len(all_positions) >= limit:
            break
    
    return all_positions[:limit]


def get_all_roots() -> list:
    """Retorna todas las notas de la escala cromática."""
    return CHROMATIC_SCALE.copy()


def get_all_chord_types() -> list:
    """Retorna todos los tipos de acordes soportados."""
    return list(CHORD_TYPES.keys())
