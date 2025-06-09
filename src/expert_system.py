import flet as ft

def main(page: ft.Page):
    page.title = "Diagnóstico de Microondas"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.ALWAYS

    preguntas = {
        0: "¿El microondas enciende?",
        1: "¿Gira la bandeja?",
        2: "¿Calienta?",
        3: "¿Hace ruidos extraños?",
        4: "¿Está bien cerrada la puerta?",
        5: "¿Está conectado a la corriente?",
        6: "¿Se encienden las luces o el display?"
    }

    decisiones = {
        10: "Funciona correctamente",
        11: "Magnetrón dañado",
        12: "Falla en el transformador",
        13: "Motor de bandeja defectuoso",
        14: "Interruptor de puerta dañado",
        15: "Falla en la tarjeta de control",
        16: "Fusible interno quemado",
        17: "Conectar el microondas"
    }

    # Diccionario para manejar el índice de la pregunta actual y las respuestas
    # El índice 0 es la pregunta inicial, y las respuestas se almacenan en una lista
    indice = {"valor": 0}
    respuestas = [] 

    # Texto para mostrar el diagnóstico final
    diagnostico_text = ft.Text("", size=22, color="red", weight="bold")

    # Funcion para mostrar el diagnóstico final basado en la decisión tomada
    def mostrar_diagnostico(key):
        diagnostico_text.value = f"Diagnóstico: {decisiones[key]}"
        question.value = ""
        botones.controls.clear()
        update_arbol()
        page.update()

    # Función para manejar la respuesta del usuario y avanzar en el árbol de decisiones
    # Actualiza el índice de la pregunta actual y muestra la siguiente pregunta o diagnóstico final
    # 0: ¿El microondas enciende?
    # ├── Sí → 1: ¿Gira la bandeja?
    # │   ├── Sí → 2: ¿Calienta?
    # │   │   ├── Sí → 10: Funciona correctamente 
    # │   │   └── No → 3: ¿Hace ruidos extraños?
    # │   │       ├── Sí → 11: Magnetrón dañado
    # │   │       └── No → 12: Falla en el transformador
    # │   └── No → 4: ¿Está bien cerrada la puerta?
    # │       ├── Sí → 13: Motor de bandeja defectuoso
    # │       └── No → 14: Interruptor de puerta dañado
    # └── No → 5: ¿Está conectado a la corriente?
    #     ├── Sí → 6: ¿Se encienden las luces o el display?
    #     │   ├── Sí → 15: Falla en la tarjeta de control
    #     │   └── No → 16: Fusible interno quemado
    #     └── No → 17: Conectar el microondas

    def siguiente_pregunta(respuesta):
        respuestas.append(respuesta)

        val = indice["valor"]
        if val == 0:
            indice["valor"] = 1 if respuesta == "Sí" else 5
        elif val == 1:
            indice["valor"] = 2 if respuesta == "Sí" else 4
        elif val == 2:
            indice["valor"] = 10 if respuesta == "Sí" else 3
        elif val == 3:
            indice["valor"] = 11 if respuesta == "Sí" else 12
        elif val == 4:
            indice["valor"] = 13 if respuesta == "Sí" else 14
        elif val == 5:
            indice["valor"] = 6 if respuesta == "Sí" else 17
        elif val == 6:
            indice["valor"] = 15 if respuesta == "Sí" else 16

        if indice["valor"] in decisiones:
            mostrar_diagnostico(indice["valor"])
        else:
            question.value = preguntas.get(indice["valor"], "")
            update_arbol()
            page.update()

    # Función para reiniciar el sistema y volver al inicio
    # Resetea el índice, las respuestas y actualiza la interfaz
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

    # Función para crear un nodo del árbol de decisiones
    # Cada nodo muestra un número, un texto y un color basado en el estado de la pregunta
    def nodo_arbol(numero, texto):
        color = "grey"
        # Determina el color del nodo basado en la respuesta y el estado actual
        if numero == indice["valor"]:
            color = "green" if numero < 10 else "red"
        elif numero in respuestas_visitadas():
            color = "blue"
        return ft.Column([
            ft.CircleAvatar(
                # Muestra el número del nodo, o "D" si es una decisión final
                content=ft.Text(str(numero + 1) if numero < 10 else "D", color="white"),
                bgcolor=color,
                radius=25
            ),
            ft.Text(texto, size=12, text_align="center")
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    # Función para obtener las respuestas visitadas en el árbol de decisiones
    # Devuelve una lista de nodos visitados basados en las respuestas dadas
    def respuestas_visitadas():
        visitados = []
        val = 0
        # Recorre las respuestas y actualiza el valor del nodo basado en las decisiones
        for r in respuestas:
            visitados.append(val)
            # Actualiza el valor del nodo basado en la respuesta
            
            if val == 0: #Ejemplo: pregunta 0 
                val = 1 if r == "Sí" else 5  
            elif val == 1:
                val = 2 if r == "Sí" else 4
            elif val == 2:
                val = 10 if r == "Sí" else 3 
            elif val == 3:
                val = 11 if r == "Sí" else 12 
            elif val == 4:
                val = 13 if r == "Sí" else 14 
            elif val == 5:
                val = 6 if r == "Sí" else 17 
            elif val == 6:
                val = 15 if r == "Sí" else 16 
            if val in decisiones:
                visitados.append(val)
                break
        return visitados

    # Función para actualizar el árbol de decisiones en la interfaz
    # Limpia los controles del árbol y los vuelve a construir con los nodos actuales
    def update_arbol():
        arbol.controls.clear()
        arbol.controls.append(
            ft.Column([
                ft.Row([ft.Container(nodo_arbol(0, preguntas[0]), padding=10)
                ],alignment=ft.MainAxisAlignment.CENTER), # Nodo raíz
                ft.Row([
                    ft.Container(width=300),  # Espacio a la izquierda
                    ft.Container(nodo_arbol(1, preguntas[1]), padding=10), # Nodo 1
                    ft.Container(width=450),
                    ft.Container(nodo_arbol(5, preguntas[5]), padding=10), # Nodo 5
                ], alignment=ft.MainAxisAlignment.START),
                ft.Row([
                    ft.Container(width=120), 
                    ft.Container(nodo_arbol(2, preguntas[2]), padding=10), # Nodo 2
                    ft.Container(width=205), 
                    ft.Container(nodo_arbol(4, preguntas[4]), padding=10), # Nodo 4
                    ft.Container(width=165), 
                    ft.Container(nodo_arbol(6, preguntas[6]), padding=10), # Nodo 6
                    ft.Container(width=10), 
                    ft.Container(nodo_arbol(17, decisiones[17]), padding=10), # Nodo 17
                ], alignment=ft.MainAxisAlignment.START),
                ft.Row([
                    ft.Container(width=1),  # Espacio a la izquierda
                    ft.Container(nodo_arbol(10, decisiones[10]),padding=5), # Nodo 10
                    ft.Container(width=5),  # Espacio entre nodos
                    ft.Container(nodo_arbol(3, preguntas[3]), padding=5), # Nodo 3
                    ft.Container(width=5),
                    ft.Container(nodo_arbol(13, decisiones[13]), padding=5), # Nodo 13
                    ft.Container(width=5),
                    ft.Container(nodo_arbol(14, decisiones[14]), padding=5), # Nodo 14
                    ft.Container(width=5),
                    ft.Container(nodo_arbol(15, decisiones[15]), padding=5), # Nodo 15
                    ft.Container(width=5),
                    ft.Container(nodo_arbol(16, decisiones[16]), padding=5), # Nodo 16
                ], alignment=ft.MainAxisAlignment.START),
                ft.Row([
                    ft.Container(width=90),  # Espacio a la izquierda para alinear bajo el nodo padre
                    ft.Container(nodo_arbol(11, decisiones[11]), padding=10),
                    ft.Container(width=10),  # Espacio entre los nodos
                    ft.Container(nodo_arbol(12, decisiones[12]), padding=10),
                ], alignment=ft.MainAxisAlignment.START),
            ])
        )
        page.update()

    # Inicializa la pregunta actual y los botones de respuesta
    question = ft.Text(preguntas[indice["valor"]], size=20, weight="bold", text_align=ft.TextAlign.CENTER)

    botones = ft.Row([
        ft.ElevatedButton("Sí", on_click=lambda _: siguiente_pregunta("Sí")),
        ft.ElevatedButton("No", on_click=lambda _: siguiente_pregunta("No")),
    ], alignment=ft.MainAxisAlignment.CENTER)

    # Inicializa el árbol de decisiones
    # Crea un contenedor para el árbol y lo actualiza con los nodos iniciales
    arbol = ft.Column()
    update_arbol()

    # Agrega los controles al page
    page.add(
        ft.Container(
            content=ft.Column(
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
                spacing=20,
            ),
            expand=True,
            padding=20,
            bgcolor=ft.Colors.WHITE,
        )
    )

    page.update()

ft.app(target=main)