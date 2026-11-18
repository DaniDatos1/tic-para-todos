# Matriz de casos de prueba

Ejecución: 2026-11-17. Aprobados: 49 de 49 (100 %).

| ID | Req. | Descripción | Resultado |
|---|---|---|---|
| CP-01 | RF01 | Registro con nombre, celular y PIN sin correo | Aprobado |
| CP-02 | RF13 | Registro rechazado si no acepta el tratamiento de datos | Aprobado |
| CP-03 | RF01 | Registro rechazado con celular duplicado | Aprobado |
| CP-04 | RF01 | Validación de formato de celular (10 dígitos) y PIN (4 dígitos) | Aprobado |
| CP-05 | RF13 | El consentimiento queda registrado con fecha y versión | Aprobado |
| CP-06 | RF02 | Inicio de sesión con celular y PIN correctos | Aprobado |
| CP-07 | RF02 | Inicio de sesión rechazado con PIN incorrecto | Aprobado |
| CP-08 | RNF05 | El PIN se almacena cifrado con bcrypt, nunca en texto plano | Aprobado |
| CP-09 | RNF05 | Las rutas protegidas exigen sesión válida | Aprobado |
| CP-10 | RF03 | La prueba diagnóstica tiene 10 preguntas | Aprobado |
| CP-11 | RF03 | El diagnóstico recomienda el primer módulo no dominado | Aprobado |
| CP-12 | RF03 | El diagnóstico se rechaza si faltan respuestas | Aprobado |
| CP-13 | RF04 | Las rutas muestran los cuatro módulos y el recomendado | Aprobado |
| CP-14 | RF05 | Cada lección presenta título, propósito y pasos | Aprobado |
| CP-15 | RF06 | La actividad no expone la respuesta correcta antes de responder | Aprobado |
| CP-16 | RF06 | Respuesta incorrecta: explica por qué no es y no revela la correcta | Aprobado |
| CP-17 | RF06 | Respuesta correcta: retroalimentación con explicación | Aprobado |
| CP-18 | RF07 | El progreso se registra y se recuerda la última lección vista | Aprobado |
| CP-19 | RF08 | No se entrega certificado si el módulo no está terminado | Aprobado |
| CP-20 | RF08 | Se genera el certificado PDF al terminar el módulo | Aprobado |
| CP-21 | RF09 | El facilitador crea un grupo | Aprobado |
| CP-22 | RF09 | El facilitador inscribe a un aprendiz y consulta su avance | Aprobado |
| CP-23 | RF02 | El facilitador restablece el PIN de un aprendiz de su grupo | Aprobado |
| CP-24 | RF09 | Un aprendiz no puede acceder al panel del facilitador | Aprobado |
| CP-25 | RF10 | Crear (C) un módulo | Aprobado |
| CP-26 | RF10 | Consultar (R) y modificar (U) un módulo | Aprobado |
| CP-27 | RF10 | Crear una lección con su actividad sin modificar el código | Aprobado |
| CP-28 | RF10 | Modificar una lección y validar una sola opción correcta | Aprobado |
| CP-29 | RF10 | Eliminar (D) una lección y un módulo | Aprobado |
| CP-30 | RF10 | Gestión de usuarios: crear, editar y desactivar | Aprobado |
| CP-31 | RF10 | Un aprendiz no puede usar las funciones de administración | Aprobado |
| CP-32 | RF11 | Exportar el reporte de progreso en CSV | Aprobado |
| CP-33 | RF12 | La interfaz incluye controles de letra, contraste, voz y ayuda | Aprobado |
| CP-34 | RNF09 | La PWA expone manifiesto y service worker | Aprobado |
| CP-35 | RF05 | Todas las lecciones traen situación real, consejos, palabras clave y resumen | Aprobado |
| CP-36 | RF06 | Cada lección tiene dos preguntas: una de recordar/comprender y una de aplicar/analizar | Aprobado |
| CP-37 | RF07 | La lección se completa solo al acertar todas sus preguntas | Aprobado |
| CP-38 | RF06 | Cada opción incorrecta tiene su propia explicación de por qué no es | Aprobado |
| CP-39 | RF06 | La opción correcta no ocupa siempre la misma posición | Aprobado |
| CP-40 | RNF05 | La cuenta se bloquea tras 5 intentos fallidos de PIN | Aprobado |
| CP-41 | RNF05 | No se permiten PIN fáciles de adivinar (1234, 0000, 9876) | Aprobado |
| CP-42 | RNF05 | El servidor envía cabeceras de seguridad HTTP | Aprobado |
| CP-43 | RNF05 | El reporte CSV neutraliza fórmulas maliciosas en los nombres | Aprobado |
| CP-44 | RF02 | Se puede entrar como invitado sin dar ningún dato personal | Aprobado |
| CP-45 | RF02 | El invitado vuelve a entrar desde su dispositivo y conserva su avance | Aprobado |
| CP-46 | RF01 | El invitado guarda su avance con nombre, celular y PIN sin perder lo hecho | Aprobado |
| CP-47 | RF08 | El invitado debe guardar su avance para recibir certificados | Aprobado |
| CP-48 | RNF05 | Detrás de un túnel, el límite de invitados se cuenta por la IP real de cada visitante | Aprobado |
| CP-49 | RNF05 | En un despliegue público no se crean los usuarios de prueba, solo el administrador configurado | Aprobado |
