import flet as ft

def main(page: ft.Page):
    page.title = "Trolli App"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0

    selected_color = ft.Ref[ft.Container]()
    color_selected_value = ft.Ref[str]()
    list_name_field = ft.Ref[ft.TextField]()

    # Lista de colores
    colors = [
        "#60BD68", "#F15854", "#FAA43A", "#5DA5DA",
        "#F17CB0", "#B276B2", "#DECF3F", "#4D4D4D",
        "#B2912F", "#FFB347", "#FF6961", "#77DD77",
        "#AEC6CF", "#CFCFC4", "#836953", "#03C03C"
    ]

    def open_modal(e):
        page.dialog = dialog
        dialog.open = True
        page.update()

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
            page.snack_bar = ft.SnackBar(ft.Text(f"Lista '{name}' creada con color {color}"))
            page.snack_bar.open = True
        close_modal()

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
        content=ft.Column([
            ft.TextField(ref=list_name_field, label="New List Name"),
            ft.Text("Choose a color:", size=14),
            color_boxes
        ]),
        actions=[
            ft.TextButton("Cancel", on_click=close_modal),
            ft.ElevatedButton("Create", on_click=create_list)
        ],
        actions_alignment=ft.MainAxisAlignment.END
    )

    # Navbar lateral (como en la imagen)
    sidebar = ft.Container(
        width=200,
        bgcolor="#F2F2F2",
        padding=20,
        content=ft.Column([
            ft.Text("Workspace", size=18, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Text("📋 Boards"),
            ft.Text("👥 Members"),
            ft.Divider(),
            ft.Text("▶ My First Board", size=16),
            ft.Text("➕ New Project", size=16),
        ], spacing=15)
    )

    # Botón de agregar lista
    main_area = ft.Container(
        expand=True,
        padding=30,
        content=ft.Column([
            ft.ElevatedButton("+ add a list", on_click=open_modal)
        ])
    )

    # Header superior
    header = ft.Container(
        height=60,
        bgcolor="#0B79D0",
        padding=15,
        content=ft.Text("Trolli", size=25, weight="bold", color=ft.Colors.WHITE),
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
        ], expand=True)
    )

ft.app(target=main)
