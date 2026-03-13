"""
Kuatrolele - Generador de Acordes para Instrumentos de 4 Cuerdas
Interfaz de usuario con Flet
"""

import flet as ft
from music_engine import (
    generate_chords,
    get_all_roots,
    get_all_chord_types,
    parse_note
)


def main(page: ft.Page):
    page.title = "Kuatrolele - Generador de Acordes"
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(color_scheme_seed="blue")
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    # Campos de afinación (Cuerda 4 = más grave, Cuerda 1 = más aguda)
    string_fields = [
        ft.TextField(
            label="Cuerda 4",
            value="F3",
            width=120,
            text_align=ft.TextAlign.CENTER,
        ),
        ft.TextField(
            label="Cuerda 3",
            value="A#3",
            width=120,
            text_align=ft.TextAlign.CENTER,
        ),
        ft.TextField(
            label="Cuerda 2",
            value="D4",
            width=120,
            text_align=ft.TextAlign.CENTER,
        ),
        ft.TextField(
            label="Cuerda 1",
            value="G4",
            width=120,
            text_align=ft.TextAlign.CENTER,
        ),
    ]

    frets_field = ft.TextField(
        label="Trastes",
        value="14",
        width=100,
        text_align=ft.TextAlign.CENTER,
        keyboard_type=ft.KeyboardType.NUMBER,
    )

    # Dropdowns de filtros
    root_dropdown = ft.Dropdown(
        label="Nota Raíz",
        width=150,
        value="Cualquiera",
        options=[ft.dropdown.Option("Cualquiera")] + [
            ft.dropdown.Option(note) for note in get_all_roots()
        ],
    )

    type_dropdown = ft.Dropdown(
        label="Tipo de Acorde",
        width=150,
        value="Cualquiera",
        options=[ft.dropdown.Option("Cualquiera")] + [
            ft.dropdown.Option(chord_type) for chord_type in get_all_chord_types()
        ],
    )

    # Filtro de cuerda específica
    string_filter_dropdown = ft.Dropdown(
        label="Cuerda",
        width=120,
        value="Ninguna",
        options=[
            ft.dropdown.Option("Ninguna"),
            ft.dropdown.Option("1"),
            ft.dropdown.Option("2"),
            ft.dropdown.Option("3"),
            ft.dropdown.Option("4"),
        ],
    )

    string_fret_field = ft.TextField(
        label="Traste fijo",
        value="",
        hint_text="0-14",
        width=100,
        text_align=ft.TextAlign.CENTER,
        keyboard_type=ft.KeyboardType.NUMBER,
    )

    # Contenedor de resultados: ResponsiveRow para columnas según ancho de pantalla.
    # Móvil (xs): 1 columna. Tablet (sm): 2. Desktop (md+): 3. Cada tarjeta altura natural.
    results_grid = ft.ResponsiveRow(
        controls=[],
        spacing=12,
        run_spacing=12,
    )

    results_container = ft.Container(
        content=results_grid,
        border=ft.Border.all(1, ft.Colors.OUTLINE),
        border_radius=10,
        padding=10,
    )

    # Indicador de carga y contador
    loading_indicator = ft.ProgressRing(visible=False, width=20, height=20)
    results_count = ft.Text("", size=14, color=ft.Colors.SECONDARY)

    # Mensaje de error
    error_banner = ft.Banner(
        bgcolor=ft.Colors.ERROR_CONTAINER,
        leading=ft.Icon(ft.Icons.ERROR, color=ft.Colors.ERROR),
        content=ft.Text(""),
        actions=[
            ft.TextButton("Cerrar", on_click=lambda e: close_banner()),
        ],
        open=False,
    )

    def close_banner():
        error_banner.open = False
        page.update()

    def show_error(message: str):
        error_banner.content = ft.Text(message, color=ft.Colors.ON_ERROR_CONTAINER)
        error_banner.open = True
        page.update()

    def create_chord_card(chord: dict) -> ft.Card:
        """Crea una tarjeta visual para un acorde en formato tablatura."""
        frets = chord['frets']
        notes = chord['notes']
        open_strings = chord.get('open_strings', 0)
        fret_span = chord.get('fret_span', 0)
        inversion_name = chord.get('inversion_name', 'Fundamental')
        bass_note = chord.get('bass_note', '')
        inversion = chord.get('inversion', 0)
        # Índice de la cuerda que tiene el bajo real (en el array original)
        bass_string_index = chord.get('bass_string_index', 0)
        
        # Formato tablatura: cuerda 1 (aguda) arriba, cuerda 4 (grave) abajo
        # El array viene [cuerda4, cuerda3, cuerda2, cuerda1], invertimos para mostrar
        string_names = ["1", "2", "3", "4"]
        frets_reversed = list(reversed(frets))
        notes_reversed = list(reversed(notes))
        
        # Convertir bass_string_index al índice en el array invertido
        # Original: [c4, c3, c2, c1] -> Invertido: [c1, c2, c3, c4]
        # Original idx 0 (c4) -> Invertido idx 3
        # Original idx 3 (c1) -> Invertido idx 0
        bass_display_index = 3 - bass_string_index
        
        # Crear filas de tablatura con fuente monoespaciada
        tab_rows = []
        for i, (string_num, fret, note) in enumerate(zip(string_names, frets_reversed, notes_reversed)):
            # Destacar cuerdas al aire con color verde
            fret_color = ft.Colors.GREEN if fret == 0 else ft.Colors.PRIMARY
            # Verificar si esta cuerda es el bajo real
            is_bass = (i == bass_display_index)
            note_display = f" ({note})" if not is_bass else f" ({note}) ← bajo"
            tab_rows.append(
                ft.Row(
                    [
                        ft.Text(
                            f"{string_num}│",
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            font_family="Consolas",
                            color=ft.Colors.SECONDARY,
                        ),
                        ft.Text(
                            f"──{fret}──",
                            size=14,
                            font_family="Consolas",
                            color=fret_color,
                        ),
                        ft.Text(
                            note_display,
                            size=12,
                            color=ft.Colors.TERTIARY if is_bass else ft.Colors.ON_SURFACE_VARIANT,
                            italic=True,
                            weight=ft.FontWeight.BOLD if is_bass else ft.FontWeight.NORMAL,
                        ),
                    ],
                    spacing=0,
                )
            )

        # Crear etiqueta de facilidad
        ease_label = []
        if open_strings > 0:
            ease_label.append(f"{open_strings} al aire")
        if fret_span > 0:
            ease_label.append(f"{fret_span} trastes")
        else:
            ease_label.append("sin extensión")
        
        ease_text = " · ".join(ease_label)
        
        # Determinar color del indicador según facilidad
        if open_strings >= 3:
            ease_color = ft.Colors.GREEN
        elif open_strings >= 2 or fret_span <= 1:
            ease_color = ft.Colors.LIGHT_GREEN
        elif fret_span <= 2:
            ease_color = ft.Colors.YELLOW
        else:
            ease_color = ft.Colors.ORANGE

        # Color de inversión
        if inversion == 0:
            inv_color = ft.Colors.BLUE_200
        else:
            inv_color = ft.Colors.PURPLE_200

        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            chord['name'],
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.PRIMARY,
                        ),
                        # Fila con inversión y facilidad
                        ft.Row(
                            [
                                ft.Container(
                                    content=ft.Text(
                                        inversion_name,
                                        size=10,
                                        color=ft.Colors.ON_SECONDARY_CONTAINER,
                                        weight=ft.FontWeight.W_500,
                                    ),
                                    bgcolor=inv_color,
                                    padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                                    border_radius=4,
                                ),
                                ft.Text(
                                    ease_text,
                                    size=10,
                                    color=ease_color,
                                ),
                            ],
                            spacing=8,
                        ),
                        ft.Divider(height=5),
                        *tab_rows,
                    ],
                    spacing=2,
                ),
                padding=15,
            ),
            elevation=3,
        )

    def generate_clicked(e):
        """Maneja el evento de generar acordes."""
        loading_indicator.visible = True
        results_count.value = "Buscando..."
        page.update()

        try:
            tuning = [field.value.strip() for field in string_fields]
            for note in tuning:
                parse_note(note)

            max_frets = int(frets_field.value)
            if max_frets < 1 or max_frets > 24:
                raise ValueError("El número de trastes debe estar entre 1 y 24")

            root_filter = None if root_dropdown.value == "Cualquiera" else root_dropdown.value
            type_filter = None if type_dropdown.value == "Cualquiera" else type_dropdown.value

            # Parsear filtro de cuerda específica
            string_fret_filter = None
            if string_filter_dropdown.value != "Ninguna" and string_fret_field.value.strip():
                string_num = int(string_filter_dropdown.value)
                fret_value = int(string_fret_field.value)
                if fret_value < 0 or fret_value > max_frets:
                    raise ValueError(f"El traste fijo debe estar entre 0 y {max_frets}")
                # Convertir número de cuerda a índice (Cuerda 4=0, 3=1, 2=2, 1=3)
                string_index = 4 - string_num
                string_fret_filter = {string_index: fret_value}

            chords = generate_chords(
                tuning=tuning,
                max_frets=max_frets,
                root_filter=root_filter,
                type_filter=type_filter,
                limit=10,
                string_fret_filter=string_fret_filter
            )

            results_grid.controls.clear()
            for chord in chords:
                card = create_chord_card(chord)
                results_grid.controls.append(
                    ft.Container(
                        content=card,
                        col={
                            ft.ResponsiveRowBreakpoint.XS: 12,   # móvil: 1 columna
                            ft.ResponsiveRowBreakpoint.SM: 6,    # tablet: 2 columnas
                            ft.ResponsiveRowBreakpoint.MD: 4,    # desktop: 3 columnas
                            ft.ResponsiveRowBreakpoint.LG: 4,
                            ft.ResponsiveRowBreakpoint.XL: 3,    # pantalla grande: 4 columnas
                        },
                    )
                )

            if chords:
                results_count.value = f"Se encontraron {len(chords)} acordes"
            else:
                results_count.value = "No se encontraron acordes con los filtros seleccionados"

        except ValueError as ex:
            show_error(f"Error de validación: {str(ex)}")
            results_count.value = ""
        except Exception as ex:
            show_error(f"Error inesperado: {str(ex)}")
            results_count.value = ""
        finally:
            loading_indicator.visible = False
            page.update()

    generate_button = ft.Button(
        "Generar Acordes",
        icon=ft.Icons.MUSIC_NOTE,
        on_click=generate_clicked,
        style=ft.ButtonStyle(
            padding=ft.Padding.symmetric(horizontal=30, vertical=15),
        ),
    )

    # Layout principal
    page.overlay.append(error_banner)

    page.add(
        ft.Column(
            [
                # Título
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.MUSIC_NOTE, size=32, color=ft.Colors.PRIMARY),
                            ft.Text(
                                "Kuatrolele",
                                size=28,
                                weight=ft.FontWeight.BOLD,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    margin=ft.Margin.only(bottom=20),
                ),

                # Sección de afinación
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "Afinación del Instrumento",
                                size=16,
                                weight=ft.FontWeight.W_500,
                            ),
                            ft.Row(
                                string_fields + [frets_field],
                                alignment=ft.MainAxisAlignment.CENTER,
                                wrap=True,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    padding=15,
                    border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                    border_radius=10,
                    margin=ft.Margin.only(bottom=15),
                ),

                # Sección de filtros
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "Filtros (Opcionales)",
                                size=16,
                                weight=ft.FontWeight.W_500,
                            ),
                            ft.Row(
                                [root_dropdown, type_dropdown],
                                alignment=ft.MainAxisAlignment.CENTER,
                                wrap=True,
                            ),
                            ft.Divider(height=15),
                            ft.Text(
                                "Fijar Traste en Cuerda",
                                size=14,
                                color=ft.Colors.SECONDARY,
                            ),
                            ft.Row(
                                [string_filter_dropdown, string_fret_field],
                                alignment=ft.MainAxisAlignment.CENTER,
                                wrap=True,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    padding=15,
                    border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                    border_radius=10,
                    margin=ft.Margin.only(bottom=15),
                ),

                # Botón y estado
                ft.Row(
                    [generate_button, loading_indicator],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=15,
                ),
                ft.Container(
                    content=results_count,
                    alignment=ft.Alignment.CENTER,
                    margin=ft.Margin.symmetric(vertical=10),
                ),

                # Resultados
                ft.Text(
                    "Acordes Encontrados",
                    size=16,
                    weight=ft.FontWeight.W_500,
                ),
                results_container,
            ],
            spacing=10,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )


if __name__ == "__main__":
    ft.run(main)
