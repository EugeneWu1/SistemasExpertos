import flet as ft

def main(page: ft.Page):
    page.title = "Mini Sistema Experto - Diagnóstico Microondas"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    preguntas = [
        "¿El microondas enciende?",
        "¿Esta conectado a la corriente?",
        "¿El panel de control funciona?",
        "¿El plato gira?",
        "¿La bandeja del microondas está correctamente colocada?",
        "¿Calienta la comida?",
        "¿El microondas hace ruidos extraños?"
    ]
    indice = {"valor": 0}

    # Función para crear la fila de progreso principal
    def get_circles():
        return ft.Row(
            [
                ft.Container(
                    content=ft.CircleAvatar(
                        radius=15,
                        bgcolor="green" if i == indice["valor"] else "grey",
                        content=ft.Text(str(i + 1), color="white", size=16)
                    ),
                    margin=ft.margin.only(right=10)
                )
                for i in range(5)
            ],
            alignment=ft.MainAxisAlignment.CENTER
        )

    # Subflujo para 1.1 y 3.3
    def get_subflow_circles():
        if question.value == "¿Esta conectado a la corriente?":
            return ft.Row(
                [
                    ft.Container(
                        content=ft.CircleAvatar(
                            radius=12,
                            bgcolor="orange",
                            content=ft.Text("1.1", color="white", size=10)
                        ),
                        margin=ft.margin.only(right=10)
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER
            )
        elif question.value == "¿La bandeja del microondas está correctamente colocada?":
            return ft.Row(
                [
                    ft.Container(
                        content=ft.CircleAvatar(
                            radius=12,
                            bgcolor="orange",
                            content=ft.Text("3.3", color="white", size=10)
                        ),
                        margin=ft.margin.only(right=10)
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER
            )
        else:
            return ft.Row([], alignment=ft.MainAxisAlignment.CENTER)

    # Controles de progreso
    circles_row = ft.Column([get_circles()], alignment=ft.MainAxisAlignment.CENTER)
    subflow_row = ft.Column([], alignment=ft.MainAxisAlignment.CENTER)

    imagen_arbol = ft.Image(
        src="https://compilandoconocimiento.com/wp-content/uploads/2017/01/bst-2.png?w=387&h=290",
        width=200,
        height=200,
        fit=ft.ImageFit.CONTAIN
    )

    question = ft.Text("¿El microondas enciende?", size=20)
    result = ft.Text("", size=18, color="blue")
    btn_yes = ft.ElevatedButton("Sí")
    btn_no = ft.ElevatedButton("No")

    # Actualizar visualización de los círculos
    def update_circles():
        circles_row.controls.clear()
        circles_row.controls.append(get_circles())

        if question.value in [
            "¿Esta conectado a la corriente?",
            "¿La bandeja del microondas está correctamente colocada?"
        ]:
            subflow_row.controls.clear()
            subflow_row.controls.append(get_subflow_circles())
        else:
            subflow_row.controls.clear()

        page.update()

    def reset():
        question.value = "¿El microondas enciende?"
        result.value = ""
        btn_yes.visible = True
        btn_no.visible = True
        indice["valor"] = 0
        subflow_row.controls.clear()
        update_circles()
        page.update()

    def on_yes(e):
        if question.value == "¿El microondas enciende?":
            question.value = "¿El panel de control funciona?"
            indice["valor"] = 1

        elif question.value == "¿Esta conectado a la corriente?":
            result.value = "Asegúrese que el cable de alimentación funcione."
            btn_yes.visible = False
            btn_no.visible = False
            indice["valor"] = 0

        elif question.value == "¿El panel de control funciona?":
            question.value = "¿El plato gira?"
            indice["valor"] = 2

        elif question.value == "¿El plato gira?":
            question.value = "¿Calienta la comida?"
            indice["valor"] = 3

        elif question.value == "¿La bandeja del microondas está correctamente colocada?":
            result.value = "Problema fisico interno."
            btn_yes.visible = False
            btn_no.visible = False
            indice["valor"] = 3

        elif question.value == "¿Calienta la comida?":
            question.value = "¿El microondas hace ruidos extraños?"
            indice["valor"] = 4

        elif question.value == "¿El microondas hace ruidos extraños?":
            result.value = "Detectar el origen del ruido y revisar la pieza fisica."
            btn_yes.visible = False
            btn_no.visible = False

        update_circles()
        page.update()

    def on_no(e):
        if question.value == "¿El microondas enciende?":
            question.value = "¿Esta conectado a la corriente?"
            btn_yes.visible = True
            btn_no.visible = True
            indice["valor"] = 0

        elif question.value == "¿Esta conectado a la corriente?":
            result.value = "Conecte el cable a la fuente de corriente."
            btn_yes.visible = False
            btn_no.visible = False
            indice["valor"] = 0

        elif question.value == "¿El panel de control funciona?":
            result.value = "Puede haber un problema con el panel de control o la fuente de alimentación."
            btn_yes.visible = False
            btn_no.visible = False
            indice["valor"] = 2

        elif question.value == "¿El plato gira?":
            question.value = "¿La bandeja del microondas está correctamente colocada?"
            btn_yes.visible = True
            btn_no.visible = True
            indice["valor"] = 2

        elif question.value == "¿La bandeja del microondas está correctamente colocada?":
            result.value = "Asegúrese que la bandeja esté bien colocada."
            btn_yes.visible = False
            btn_no.visible = False
            indice["valor"] = 3

        elif question.value == "¿Calienta la comida?":
            result.value = "Puede haber un problema con el magnetrón o el sistema de calentamiento."
            btn_yes.visible = False
            btn_no.visible = False
            indice["valor"] = 4

        elif question.value == "¿El microondas hace ruidos extraños?":
            result.value = "Contacte un tecnico especializado."
            btn_yes.visible = False
            btn_no.visible = False
            indice["valor"] = 5

        update_circles()
        page.update()

    btn_yes.on_click = on_yes
    btn_no.on_click = on_no

    # Agregar todos los elementos a la página
    page.add(
        circles_row,
        subflow_row,
        ft.Container(
            content=imagen_arbol,
            alignment=ft.alignment.center,
            padding=ft.padding.all(10)
        ),
        question,
        ft.Row([btn_yes, btn_no], alignment=ft.MainAxisAlignment.CENTER),
        result,
        ft.ElevatedButton("Reiniciar", on_click=lambda e: reset())
    )

if __name__ == "__main__":
    ft.app(target=main)
