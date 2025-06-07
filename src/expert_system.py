import flet as ft

def main(page: ft.Page):
    page.title = "Mini Sistema Experto - Diagnóstico Microondas"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER


    imagen_arbol = ft.Image(
        src="https://compilandoconocimiento.com/wp-content/uploads/2017/01/bst-2.png?w=387&h=290",
        width=800,
        height=800,
        fit=ft.ImageFit.CONTAIN
    )

    question = ft.Text("¿El microondas enciende?", size=20)
    result = ft.Text("", size=18, color="blue")
    btn_yes = ft.ElevatedButton("Sí")
    btn_no = ft.ElevatedButton("No")

    def reset():
        question.value = "¿El microondas enciende?"
        result.value = ""
        btn_yes.visible = True
        btn_no.visible = True
        page.update()

    def on_yes(e):
        if question.value == "¿El microondas enciende?":
            question.value = "¿El plato gira?"
        elif question.value == "¿El plato gira?":
            question.value = "¿Calienta la comida?"
        elif question.value == "¿Calienta la comida?":
            question.value = "¿El microondas no hace ruidos extraños?"
        elif question.value == "¿El microondas no hace ruidos extraños?":
            result.value = "El microondas funciona correctamente."
            btn_yes.visible = False
            btn_no.visible = False
        page.update()

    def on_no(e):
        if question.value == "¿El microondas enciende?":
            result.value = "Verifica si está conectado o si el fusible está dañado."
            btn_yes.visible = False
            btn_no.visible = False
        elif question.value == "¿El plato gira?":
            result.value = "Puede haber un problema con el motor del plato."
            btn_yes.visible = False
            btn_no.visible = False
        elif question.value == "¿Calienta la comida?":
            result.value = "Puede haber un problema con el magnetrón o el sistema de calentamiento."
            btn_yes.visible = False
            btn_no.visible = False
        elif question.value == "¿El microondas hace ruidos extraños?":
            result.value = "Puede haber un mal funcionamiento del motor de accionamiento, el motor del ventilador de escape o el magnetrón.Llame a un técnico."
            btn_yes.visible = False
            btn_no.visible = False
        

        page.update()

    btn_yes.on_click = on_yes
    btn_no.on_click = on_no

    page.add(
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