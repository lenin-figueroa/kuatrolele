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
CHORD_TYPES = {
    'Mayor': [0, 4, 7],
    'Menor': [0, 3, 7],
    '7ma': [0, 4, 7, 10],
    'Mayor 7': [0, 4, 7, 11],
    'Menor 7': [0, 3, 7, 10],
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
    Verifica que las notas tocadas contengan al menos la raíz y la tercera del acorde.
    """
    root_normalized = normalize_note_name(root)
    root_index = CHROMATIC_SCALE.index(root_normalized)
    intervals = CHORD_TYPES[chord_type]
    
    third_interval = intervals[1]
    third_index = (root_index + third_interval) % 12
    third_note = CHROMATIC_SCALE[third_index]
    
    played_note_names = set(played_notes)
    
    return root_normalized in played_note_names and third_note in played_note_names


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
    limit: int = 10
) -> list:
    """
    Encuentra posiciones válidas para un acorde específico.
    """
    positions = []
    root_normalized = normalize_note_name(root)
    
    fret_ranges = [range(max_frets + 1) for _ in range(4)]
    
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
    limit: int = 10
) -> list:
    """
    Función principal para generar acordes.
    
    Args:
        tuning: Lista de notas de afinación ordenadas de grave a aguda
                [Cuerda4, Cuerda3, Cuerda2, Cuerda1] (ej: ["F3", "A#3", "D4", "G4"])
        max_frets: Número máximo de trastes
        root_filter: Filtro de nota raíz (None = todas)
        type_filter: Filtro de tipo de acorde (None = Mayor y Menor)
        limit: Número máximo de resultados
    
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
                limit=remaining
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
