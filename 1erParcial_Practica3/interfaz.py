import flet as ft

def main(page: ft.Page):
    page.title = "Explore App"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.window.height = 700
    page.window.width = 400
    page.window.resizable = False
    page.window.maximizable = False
    page.scroll = "auto"
    page.bgcolor = ft.Colors.GREY_300

    # App Bar simulada
    app_bar = ft.Container(
        bgcolor="#1ebe8e",
        padding=7,
        content=ft.Row(
            [
                # Botón con menú desplegable para visibilidad
                ft.PopupMenuButton(
                    icon=ft.Icons.VISIBILITY,
                    icon_size=30,
                    icon_color="white",
                    items=[
                        ft.PopupMenuItem(text="Visible para todos", on_click=lambda e: print("Visible para todos")),
                        ft.PopupMenuItem(text="Solo amigos", on_click=lambda e: print("Solo amigos")),
                        ft.PopupMenuItem(text="Privado", on_click=lambda e: print("Privado")),
                    ]
                ),

                # Título centrado
                ft.Text("Explore", size=20, weight="bold", color="white", expand=True, text_align="center"),

                # Botón de videocámara
                ft.IconButton(
                    icon=ft.Icons.VIDEOCAM,
                    icon_size=30,
                    icon_color="white",
                    on_click=lambda e: print("Abrir cámara o video"),
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )
    )

    # Campo de búsqueda
    search = ft.Container(
        content=ft.Row(
            controls=[
                ft.Icon(name=ft.Icons.SEARCH, color=ft.Colors.GREY_300),
                ft.TextField(
                    hint_text="Search people or tags",
                    hint_style=ft.TextStyle(
                        color=ft.Colors.GREY_300,
                        weight=ft.FontWeight.BOLD,
                    ),
                    text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
                    filled=True,
                    fill_color=ft.Colors.WHITE,
                    border_radius=5,
                    border=ft.InputBorder.NONE,
                    expand=True,  # Esto hace que el TextField use el espacio restante
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.padding.symmetric(horizontal=10),
        border_radius=5,
        bgcolor=ft.Colors.WHITE,
    )

    # Botones dentro de un solo cuadro blanco con un divider vertical
    top_buttons = ft.Container(
        bgcolor=ft.Colors.WHITE,
        border_radius=5,
        padding=10,
        content=ft.Row(
            controls=[
                # Botón 1
                ft.OutlinedButton(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.STAR, size=30, color="orange"),
                            ft.Text("Popular Now", weight="bold", size=15, color="black"),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=0),
                        side=ft.BorderSide(color=ft.Colors.WHITE, width=0),  # borde invisible
                        overlay_color=ft.Colors.with_opacity(0.05, ft.Colors.BLACK),
                        padding=ft.padding.all(10),
                    ),
                    expand=True,
                    on_click=lambda e: print("Popular Now"),
                ),

                # Divider visible
                ft.Container(
                    content=ft.VerticalDivider(
                        width=0,
                        color=ft.Colors.GREY_400,
                        thickness=2,
                    ),
                    height=60,  # Importante para que el divider se muestre
                ),

                # Botón 2
                ft.OutlinedButton(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.ARROW_UPWARD, size=30, color="skyblue"),
                            ft.Text("On the Rise", weight="bold", size=15, color="black"),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=0),
                        side=ft.BorderSide(color=ft.Colors.WHITE, width=0),  # borde invisible
                        overlay_color=ft.Colors.with_opacity(0.05, ft.Colors.BLACK),
                        padding=ft.padding.all(10),
                    ),
                    expand=True,
                    on_click=lambda e: print("On the Rise"),
                ),
            ],
            spacing=0,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )

    # Sección de canales
    def channel_row(color, image_path, title, on_click=None):
        return ft.GestureDetector(
            mouse_cursor="click",
            on_tap=on_click,
            content=ft.Container(
                bgcolor=color,
                padding=15,
                border_radius=5,
                content=ft.Row(
                    [
                        ft.Image(
                            src=image_path,
                            width=50,
                            height=50,
                            fit=ft.ImageFit.CONTAIN
                        ),
                        ft.Text(title, size=25, weight="bold", color="white", expand=True),
                    ]
                )
            )
        )

    channels = ft.Column(
        controls=[
            ft.Text("Channels", weight="bold", size=16, color=ft.Colors.GREY_600, text_align="center"),
            channel_row("#EC407A", "assets/comedy.png", "Comedy", on_click=lambda e: print("Comedy clicked")),
            channel_row("#FFB74D", "assets/art.png", "Art & Experimental", on_click=lambda e: print("Art clicked")),
            channel_row("#424242", "assets/scary.png", "Scary", on_click=lambda e: print("Scary clicked")),
            channel_row("#42A5F5", "assets/cats.png", "Cats", on_click=lambda e: print("Cats clicked")),
        ],
        spacing=10,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    page.add(
        ft.Column(
            [
                app_bar,
                ft.Container(search, padding=10),
                ft.Container(top_buttons, padding=10),
                ft.Container(channels, padding=10),
            ],
            spacing=2,
            expand=True
        )
    )

ft.app(target=main, assets_dir="assets")