import flet as ft
import requests
import json
import os

def main(page: ft.Page):
    page.title = "Trolli App"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0

    color_selected_value = ft.Ref[str]()
    list_name_field = ft.Ref[ft.TextField]()

    # Lista de colores
    colors = [
        "#60BD68", "#F15854", "#FAA43A", "#5DA5DA",
        "#F17CB0", "#B276B2", "#DECF3F", "#4D4D4D",
        "#B2912F", "#FFB347", "#FF6961", "#77DD77",
        "#AEC6CF", "#CFCFC4", "#836953", "#03C03C",
        "#6B5B95", "#88B04B",
    ]

    def close_modal(e=None):
        dialog.open = False
        page.update()

    def choose_color(e):
        color_selected_value.current = e.control.bgcolor
        for c in color_boxes.controls:
            c.border = None
        e.control.border = ft.border.all(3, ft.Colors.BLACK)
        page.update()

    def create_list(e):
        name = list_name_field.current.value
        color = color_selected_value.current or "#60BD68"
        if name.strip():
            # Enviar datos a Node-RED
            try:
                response = requests.post(
                    "http://localhost:1880/nueva-lista",  # URL de Node-RED
                    json={"nombre": name, "color": color},
                    timeout=2
                )
                if response.status_code == 200:
                    # Crear la tarjeta/lista visual
                    main_area_column.controls.append(
                        ft.Container(
                            bgcolor=color,
                            border_radius=10,
                            padding=15,
                            margin=ft.margin.only(bottom=10),
                            content=ft.Text(name, size=18, color="white")
                        )
                    )
                    page.update()

                    # SnackBar de éxito
                    page.open(
                        ft.SnackBar(
                            content=ft.Text("✅ Lista creada exitosamente 🎉"),
                            bgcolor=ft.Colors.GREEN,
                            duration=3000
                        )
                    )
                else:
                    # Error de respuesta de Node-RED
                    page.open(
                        ft.SnackBar(
                            content=ft.Text("❌ Error al guardar la lista en Node-RED."),
                            bgcolor=ft.Colors.RED,
                            duration=3000
                        )
                    )
            except Exception as err:
                print("Error al enviar a Node-RED:", err)
                # SnackBar de error de conexión
                page.open(
                    ft.SnackBar(
                        content=ft.Text("🚫 No se pudo conectar a Node-RED."),
                        bgcolor=ft.Colors.RED,
                        duration=3000
                    )
                )
        
        close_modal()


    def load_saved_lists(area_destino):
        # Ubica la carpeta Descargas del sistema
        downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        archivo_txt = os.path.join(downloads_dir, "listas_guardadas.txt")

        if not os.path.exists(archivo_txt):
            print("Archivo no encontrado:", archivo_txt)
            return

        with open(archivo_txt, "r", encoding="utf8") as f:
            for linea in f:
                try:
                    lista = json.loads(linea.strip())  # Cada línea es un JSON
                    nombre = lista.get("nombre", "Sin nombre")
                    color = lista.get("color", "#60BD68")

                    area_destino.controls.append(
                        ft.Container(
                            bgcolor=color,
                            border_radius=10,
                            padding=15,
                            margin=ft.margin.only(bottom=10),
                            content=ft.Text(nombre, size=18, color="white")
                        )
                    )
                except json.JSONDecodeError:
                    print("Línea no válida:", linea.strip())

    def check_item_clicked(e):
        e.control.checked = not e.control.checked
        page.update()
        

    # Modal
    color_boxes = ft.Row(
        controls=[
            ft.Container(
                width=30,
                height=30,
                bgcolor=color,
                border_radius=15,
                on_click=choose_color
            ) for color in colors
        ],
        wrap=True,
        spacing=10,
        run_spacing=10
    )

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Name your new list"),
        content=ft.Container(
            width= 100,  # Ancho deseado
            height= 225,  # Alto deseado
            content=ft.Column([
                ft.TextField(ref=list_name_field, label="New List Name"),
                ft.Text("Choose a color:", size=14),
                color_boxes
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)  # Alineación horizontal
        ),
        actions=[
            ft.TextButton("Cancel", on_click=close_modal),

            ft.ElevatedButton("Create", on_click=create_list)
        ],
        actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN
    )

    # Navbar lateral (como en la imagen)
    sidebar = ft.Container(
        width=200,
        bgcolor="#D6D3D3",
        padding=20,
        content=ft.Column([
            ft.Text("Workspace", size=18, weight=ft.FontWeight.BOLD),
            ft.Divider(color=ft.Colors.BLACK, thickness=1),
            #botones de navegación
            ft.TextButton("📋 Boards", style=ft.ButtonStyle(bgcolor="transparent", color="black")),
            ft.TextButton("👥 Members", style=ft.ButtonStyle(bgcolor="transparent", color="black")),
            ft.Divider(color=ft.Colors.BLACK, thickness=1),
            ft.TextButton("▶ My First Board", style=ft.ButtonStyle(bgcolor="transparent", color="black"),),
            ft.TextButton("➕ New Project", style=ft.ButtonStyle(bgcolor="transparent", color="black")),
        ], spacing=15)
    )

    main_area_column = ft.Column(
        scroll="auto",
        expand=True, 
    )

    main_area = ft.Container(
        expand=True,
        padding=30,
        content=main_area_column,
    )


    # Botón de agregar lista (debe estar siempre arriba)
    main_area_column.controls.insert(
        0,
        ft.ElevatedButton(
            icon=ft.Icons.ADD,
            icon_color="#064E85",
            text="Add a list",
            width=150,
            bgcolor="#C4DBEC",
            style=ft.ButtonStyle(
                color="#064E85"
            ),
            on_click=lambda e: page.open(dialog),
        ),
    )

    # Header superior
    header = ft.Container(
        height=60,
        bgcolor="#0B79D0",
        padding=15,
        content=ft.Row(
            [
                ft.Icon(ft.Icons.ADD, color=ft.Colors.WHITE, size=36),  # Icono + a la izquierda
                ft.Text("Trolli", size=25, weight="bold", color=ft.Colors.WHITE),
                ft.Container(expand=True),  # Espaciador flexible
                ft.PopupMenuButton(
                    icon_color=ft.Colors.WHITE,
                    tooltip="Options",
                    items=[
                        ft.PopupMenuItem(text="Item 1"),
                        ft.PopupMenuItem(icon=ft.Icons.POWER_INPUT, text="Check power"),
                        ft.PopupMenuItem(
                            content=ft.Row(
                                [
                                    ft.Icon(ft.Icons.HOURGLASS_TOP_OUTLINED),
                                    ft.Text("Item with a custom content"),
                                ]
                            ),
                            on_click=lambda _: print("Button with custom content clicked!"),
                        ),
                        ft.PopupMenuItem(),  # divider
                        ft.PopupMenuItem(
                            text="Checked item", checked=False, on_click=check_item_clicked
                        ),
                    ]
                )
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,  # Centrado vertical
        ),
        alignment=ft.alignment.center_left
    )

    

    # Layout final
    page.add(
        ft.Column([
            header,
            ft.Row([
                sidebar,
                main_area
            ], expand=True)
        ], expand=True, spacing=0)
    )

    load_saved_lists(main_area_column)
    page.update()

ft.app(target=main)
