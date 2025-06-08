import flet as ft

def main(page: ft.Page):
    page.title = "Diagnóstico de Microondas"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    preguntas = {
        0: "¿El microondas enciende?",
        1: "¿Gira la bandeja?",
        2: "¿Calienta el microondas?",
        3: "¿Está conectado a la corriente?",
        4: "¿Hace ruidos extraños al funcionar?",
        5: "¿El teclado responde al presionar botones?",
        6: "¿Se apaga repentinamente?"
    }

    decisiones = {
        10: "Microondas funcionando correctamente",
        11: "Fallo en el magnetrón",
        12: "Motor de bandeja defectuoso",
        13: "Tarjeta electrónica dañada",
        14: "Conectar el microondas",
        15: "Verificar el teclado",
        16: "Problema de sobrecalentamiento",
        17: "Problema desconocido"
    }

    indice = {"valor": 0}
    respuestas = []

    diagnostico_text = ft.Text("", size=22, color="red", weight="bold")

    def mostrar_diagnostico(key):
        diagnostico_text.value = f"Diagnóstico: {decisiones[key]}"
        question.value = ""
        botones.controls.clear()
        page.update()

    def siguiente_pregunta(respuesta):
        respuestas.append(respuesta)

        # Lógica del árbol binario
        val = indice["valor"]
        if val == 0:
            indice["valor"] = 1 if respuesta == "Sí" else 3
        elif val == 1:
            indice["valor"] = 2 if respuesta == "Sí" else 12
        elif val == 2:
            indice["valor"] = 10 if respuesta == "Sí" else 11
        elif val == 3:
            indice["valor"] = 13 if respuesta == "Sí" else 14
        elif val == 4:
            indice["valor"] = 16 if respuesta == "Sí" else 17
        elif val == 5:
            indice["valor"] = 15 if respuesta == "No" else 4
        elif val == 6:
            indice["valor"] = 4 if respuesta == "Sí" else 5

        elif val >= 10:
            mostrar_diagnostico(val)
            update_arbol()
            return

        if indice["valor"] >= 10:
            mostrar_diagnostico(indice["valor"])
        else:
            question.value = preguntas.get(indice["valor"], "")
            update_arbol()
            page.update()


    def reiniciar(_):
        indice["valor"] = 0
        respuestas.clear()
        question.value = preguntas[indice["valor"]]
        diagnostico_text.value = ""
        botones.controls.clear()
        botones.controls.extend([
            ft.ElevatedButton("Sí", on_click=lambda _: siguiente_pregunta("Sí")),
            ft.ElevatedButton("No", on_click=lambda _: siguiente_pregunta("No")),
        ])
        update_arbol()
        page.update()


    def nodo_arbol(numero, texto):
        color = (
            "green" if numero == indice["valor"]
            else "blue" if numero in respuestas_visitadas()
            else "grey"
        )
        return ft.Column([
            ft.CircleAvatar(
                content=ft.Text(str(numero + 1) if numero < 10 else "D", color="white"),
                bgcolor=color,
                radius=25
            ),
            ft.Text(texto, size=12, text_align="center")
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    def respuestas_visitadas():
        visitados = []
        val = 0
        for r in respuestas:
            visitados.append(val)
            if val == 0:
                val = 1 if r == "Sí" else 3
            elif val == 1:
                val = 2 if r == "Sí" else 12
            elif val == 2:
                val = 10 if r == "Sí" else 11
            elif val == 3:
                val = 13 if r == "Sí" else 14
            elif val == 4:
                val = 16 if r == "Sí" else 17
            elif val == 5:
                val = 15 if r == "No" else 4
            elif val == 6:
                val = 4 if r == "Sí" else 5
            elif val >= 10:
                break
        return visitados


    def update_arbol():
        arbol.controls.clear()
        arbol.controls.append(
            ft.Column([
                ft.Row([ft.Container(nodo_arbol(0, preguntas[0]), padding=10)], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([
                    ft.Container(nodo_arbol(1, preguntas[1]), padding=10),
                    ft.Container(nodo_arbol(3, preguntas[3]), padding=10)
                ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
                ft.Row([
                    ft.Container(nodo_arbol(2, preguntas[2]), padding=10),
                    ft.Container(nodo_arbol(12, decisiones[12]), padding=10),
                    ft.Container(nodo_arbol(13, decisiones[13]), padding=10),
                    ft.Container(nodo_arbol(14, decisiones[14]), padding=10)
                ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
                ft.Row([
                    ft.Container(nodo_arbol(10, decisiones[10]), padding=10),
                    ft.Container(nodo_arbol(11, decisiones[11]), padding=10)
                ], alignment=ft.MainAxisAlignment.SPACE_AROUND)
            ])
        )
        page.update()


    question = ft.Text(preguntas[indice["valor"]], size=20, weight="bold", text_align=ft.TextAlign.CENTER)

    botones = ft.Row([
        ft.ElevatedButton("Sí", on_click=lambda _: siguiente_pregunta("Sí")),
        ft.ElevatedButton("No", on_click=lambda _: siguiente_pregunta("No")),
    ], alignment=ft.MainAxisAlignment.CENTER)

    arbol = ft.Column()
    update_arbol()

    page.add(
        ft.Column(
            [
                ft.Text("Sistema Experto: Diagnóstico de Microondas", size=24, weight="bold"),
                arbol,
                ft.Divider(),
                question,
                botones,
                diagnostico_text,
                ft.ElevatedButton("Reiniciar", on_click=reiniciar)
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20
        )
    )

ft.app(target=main)