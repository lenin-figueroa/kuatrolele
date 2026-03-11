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

    # Campos de afinación
    string_fields = [
        ft.TextField(
            label="Cuerda 1",
            value="F3",
            width=100,
            text_align=ft.TextAlign.CENTER,
        ),
        ft.TextField(
            label="Cuerda 2",
            value="A#3",
            width=100,
            text_align=ft.TextAlign.CENTER,
        ),
        ft.TextField(
            label="Cuerda 3",
            value="D4",
            width=100,
            text_align=ft.TextAlign.CENTER,
        ),
        ft.TextField(
            label="Cuerda 4",
            value="G4",
            width=100,
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

    # Contenedor de resultados
    results_grid = ft.GridView(
        expand=True,
        runs_count=3,
        max_extent=250,
        child_aspect_ratio=1.2,
        spacing=10,
        run_spacing=10,
    )

    results_container = ft.Container(
        content=results_grid,
        height=400,
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
        """Crea una tarjeta visual para un acorde."""
        frets_text = []
        for i, fret in enumerate(chord['frets']):
            frets_text.append(
                ft.Text(
                    f"Cuerda {i + 1}: Traste {fret}",
                    size=13,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                )
            )

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
                        ft.Text(
                            f"Notas: {', '.join(chord['notes'])}",
                            size=12,
                            color=ft.Colors.SECONDARY,
                            italic=True,
                        ),
                        ft.Divider(height=10),
                        *frets_text,
                    ],
                    spacing=5,
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

            chords = generate_chords(
                tuning=tuning,
                max_frets=max_frets,
                root_filter=root_filter,
                type_filter=type_filter,
                limit=10
            )

            results_grid.controls.clear()
            for chord in chords:
                results_grid.controls.append(create_chord_card(chord))

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
