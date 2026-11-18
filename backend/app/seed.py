"""Datos iniciales: 4 módulos y 20 lecciones de formación TIC, prueba diagnóstica y usuarios
de prueba.

Diseño de los contenidos:
- Andragogía (Knowles): cada lección parte de una situación real de la vida cotidiana.
- Taxonomía de Bloom revisada: los pasos llevan a aplicar; la práctica tiene una pregunta de
  recordar/comprender y otra de aplicar en un caso.
- Lectura fácil: frases cortas, trato de "usted", una idea por paso.
- Cada lección indica si sus pasos se hacen en el celular o en el computador.

Se carga automáticamente si la base de datos está vacía. Para reemplazar los contenidos
(borra todos los datos, incluidos usuarios y progreso):
    python -m app.seed --reiniciar
"""
import json
import os
import re
import random
import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

from .preguntas import PREGUNTAS
from .models import Actividad, Grupo, Leccion, Modulo, Opcion, PreguntaDiagnostico, Usuario
from .schemas import pin_trivial
from .security import hash_pin


def P(icono, texto, consejo=""):
    return {"icono": icono, "texto": texto, "consejo": consejo}


CONTENIDO = [
    # =====================================================================
    dict(titulo="Alfabetización y herramientas digitales", icono="💻", nivel_bloom="Recordar y aplicar",
         descripcion="Aprenda a usar el computador y las herramientas básicas para estudiar y trabajar.",
         lecciones=[
             dict(
                 titulo="Primeros pasos con el computador",
                 dispositivo="computador",
                 para_que="Para usar un computador desde cero en actividades de estudio, trabajo y de la vida diaria.",
                 situacion="Carlos consiguió un cupo en un curso virtual, pero nunca ha usado un computador. No sabe cómo prenderlo, mover el mouse ni abrir un programa. Quiere aprender para tener mejores oportunidades de trabajo.",
                 pasos=[
                     P("🖥️", "Identifique las partes del computador: la pantalla o monitor, el teclado, el mouse y la torre o unidad central.",
                       "No todos los computadores tienen torre. En los portátiles y en algunos de escritorio todo viene en una sola pieza."),
                     P("🔌", "Revise que el equipo esté conectado a la corriente y presione el botón de encendido.",
                       "Si no prende, revise primero los cables y el tomacorriente antes de pensar que está dañado."),
                     P("🖱️", "Practique con el mouse: moverlo, hacer clic, doble clic y clic derecho.",
                       "El doble clic sirve para abrir archivos y programas. El clic derecho muestra más opciones."),
                     P("⌨️", "Explore el teclado: las letras, los números, la barra espaciadora y la tecla Enter.",
                       "Siéntese derecho, con los pies apoyados y la pantalla a la altura de los ojos."),
                     P("🚀", "Abra un programa desde el menú de Inicio y ciérrelo con la X de la esquina de arriba. Al terminar, apague desde Inicio y luego Apagar.",
                       "No apague el computador desconectándolo: puede perder lo que no ha guardado."),
                 ],
                 glosario=[("Hardware", "Las partes físicas del computador, las que se pueden tocar."),
                           ("Software", "Los programas y aplicaciones."),
                           ("Sistema operativo", "El programa principal que permite usar el computador, como Windows."),
                           ("Mouse", "Aparato que mueve la flechita (el puntero) en la pantalla."),
                           ("Escritorio", "La pantalla principal que aparece al prender el computador.")],
                 recuerde=["El computador necesita hardware y software para funcionar.",
                           "El mouse y el teclado son la forma de darle órdenes al equipo.",
                           "Apagar desde el menú de Inicio protege su información."]),
             dict(
                 titulo="Manejo de archivos y carpetas",
                 dispositivo="computador",
                 para_que="Para organizar documentos, fotos y trabajos y encontrarlos rápido cuando los necesite.",
                 situacion="María está haciendo un curso y tiene muchos documentos en el computador. No recuerda dónde guardó sus tareas y pierde mucho tiempo buscándolas.",
                 pasos=[
                     P("📁", "Abra el Explorador de archivos, el ícono de la carpeta amarilla.",
                       "En Windows también se abre con las teclas Windows + E al mismo tiempo."),
                     P("➕", "Cree una carpeta nueva para organizar sus documentos: clic derecho, Nuevo y Carpeta.",
                       "Use nombres fáciles de reconocer, como Estudios, Trabajo o Fotos."),
                     P("📄", "Guarde cada documento dentro de la carpeta que le corresponde.",
                       "Evite dejar todo en el Escritorio: se llena y es difícil encontrar las cosas."),
                     P("✂️", "Practique copiar, cortar, pegar y cambiar el nombre de un archivo.",
                       "Ctrl + C copia, Ctrl + X corta y Ctrl + V pega. Copiar deja el original donde estaba; cortar lo mueve."),
                     P("🔎", "Busque un archivo escribiendo parte de su nombre en el buscador del Explorador.",
                       "Por eso conviene poner nombres claros, como Tarea_matematicas_semana2."),
                 ],
                 glosario=[("Archivo", "Un documento, foto o video guardado en el computador."),
                           ("Carpeta", "Espacio para agrupar y organizar archivos."),
                           ("Extensión", "Lo que va después del punto en el nombre, como .pdf o .docx. Indica el tipo de archivo."),
                           ("Copiar", "Hacer un duplicado sin quitar el original."),
                           ("Papelera", "Lugar donde quedan por un tiempo los archivos borrados.")],
                 recuerde=["Organizar los archivos le ahorra tiempo todos los días.",
                           "Copiar deja el original; cortar lo cambia de lugar.",
                           "Antes de borrar un archivo, asegúrese de que no lo necesita."]),
             dict(
                 titulo="Uso profesional del correo electrónico",
                 para_que="Para enviar y recibir mensajes y documentos de manera formal en el estudio y el trabajo.",
                 situacion="Andrés encontró una oferta de empleo que pide enviar la hoja de vida por correo electrónico. Tiene una cuenta, pero no sabe cómo escribir un mensaje formal ni cómo adjuntar el documento.",
                 pasos=[
                     P("📧", "Entre a su correo electrónico con su cuenta y su contraseña.",
                       "Nunca le dé su contraseña a otra persona, ni siquiera a quien le ayuda."),
                     P("✉️", "Toque Redactar o Nuevo mensaje.",
                       "Si tiene varias cuentas, revise que esté usando la suya y no la de otra persona."),
                     P("👤", "Escriba el correo del destinatario y un asunto claro, por ejemplo: Hoja de vida – Auxiliar de bodega.",
                       "Un buen asunto le dice a quien lo recibe de qué se trata sin abrir el mensaje."),
                     P("📝", "Escriba un saludo, explique en pocas líneas para qué escribe y despídase con su nombre completo y teléfono.",
                       "Use un lenguaje respetuoso y revise la ortografía antes de seguir."),
                     P("📎", "Adjunte el documento con el clip 📎 y revise todo antes de tocar Enviar.",
                       "Compruebe que el archivo aparece adjunto y que es el correcto."),
                 ],
                 glosario=[("Correo electrónico", "Servicio para enviar y recibir mensajes por internet."),
                           ("Destinatario", "La persona que recibe el mensaje."),
                           ("Asunto", "Título corto que resume el correo."),
                           ("Adjunto", "Archivo que se envía junto con el mensaje."),
                           ("Spam", "Correo no deseado. Llega a una carpeta aparte.")],
                 recuerde=["Un correo formal lleva asunto, saludo y despedida.",
                           "Revise el destinatario antes de enviar.",
                           "Verifique que el adjunto sea el documento correcto."]),
             dict(
                 titulo="Búsqueda inteligente de información",
                 para_que="Para encontrar información confiable en internet, ahorrar tiempo y resolver necesidades del estudio y de la vida diaria.",
                 situacion="Diana necesita saber los requisitos para inscribirse en un programa de formación. Encuentra muchas páginas, pero no sabe cuáles tienen información oficial y actualizada.",
                 pasos=[
                     P("🌐", "Abra un navegador como Chrome, Firefox o Edge.",
                       "Mantenga el navegador actualizado: las actualizaciones corrigen fallas de seguridad."),
                     P("🔎", "Escriba en el buscador palabras clave sobre lo que necesita, por ejemplo: requisitos inscripción técnico SENA Valledupar.",
                       "Entre más precisas sean las palabras, mejores resultados obtiene."),
                     P("🎯", "Ponga entre comillas una frase cuando la necesite exacta, por ejemplo: \"requisitos de inscripción\".",
                       "Las comillas hacen que el buscador muestre páginas con esas palabras juntas y en ese orden."),
                     P("🏛️", "Prefiera las páginas oficiales de las entidades e instituciones.",
                       "En Colombia, las direcciones que terminan en .gov.co pertenecen a entidades del Estado."),
                     P("📅", "Revise la fecha, el autor y de dónde sale la información.",
                       "Si dos páginas dicen cosas distintas, crea en la fuente oficial. No comparta nada sin verificarlo."),
                 ],
                 glosario=[("Navegador", "Programa para visitar páginas de internet."),
                           ("Buscador", "Herramienta para encontrar información, como Google."),
                           ("Palabras clave", "Las palabras que escribe para buscar."),
                           ("Dominio", "La parte final de la dirección de una página, como .gov.co."),
                           ("Fuente", "De dónde viene una información.")],
                 recuerde=["No toda la información de internet es confiable.",
                           "Las búsquedas precisas dan mejores resultados.",
                           "Verifique la fuente y la fecha antes de decidir."]),
             dict(
                 titulo="Creación de documentos digitales",
                 dispositivo="computador",
                 para_que="Para escribir cartas, solicitudes, trabajos y documentos laborales en el computador.",
                 situacion="José necesita escribir una solicitud para una institución educativa. Siempre ha escrito a mano y quiere aprender a hacerlo en el computador.",
                 pasos=[
                     P("📝", "Abra un procesador de texto como Word o Google Docs.",
                       "También hay opciones gratuitas, como LibreOffice Writer."),
                     P("📄", "Elija un documento en blanco y escriba el contenido.",
                       "Piense primero qué quiere decir: saludo, la solicitud y la despedida."),
                     P("🔠", "Use títulos, negrita y alineación para ordenar el texto.",
                       "Un diseño sencillo se ve más serio que uno con muchos colores y tipos de letra."),
                     P("🔍", "Revise la ortografía, los espacios y la presentación.",
                       "Las palabras subrayadas en rojo pueden tener errores. Lea todo el documento antes de terminar."),
                     P("💾", "Guarde el documento con un nombre claro y, si lo va a enviar, expórtelo como PDF.",
                       "En Word: Archivo, Guardar como y elija PDF. En Google Docs: Archivo, Descargar, PDF."),
                 ],
                 glosario=[("Procesador de texto", "Programa para escribir documentos, como Word."),
                           ("Formato", "La apariencia del texto: tamaño, negrita, alineación."),
                           ("PDF", "Tipo de archivo que se ve igual en cualquier equipo y es difícil de modificar."),
                           ("Fuente", "El tipo de letra."),
                           ("Margen", "El espacio en blanco entre el texto y el borde de la hoja.")],
                 recuerde=["Un documento digital se corrige fácil, sin volver a escribirlo.",
                           "Una presentación ordenada comunica mejor.",
                           "Revise antes de exportar a PDF y guarde una copia."]),
         ]),
    # =====================================================================
    dict(titulo="Comunicación y productividad digital", icono="💬", nivel_bloom="Comprender y aplicar",
         descripcion="Use internet para comunicarse, estudiar y trabajar con otras personas.",
         lecciones=[
             dict(
                 titulo="Comunicación responsable por WhatsApp",
                 para_que="Para comunicarse bien por mensajería, compartir información útil y participar en grupos de la comunidad.",
                 situacion="Luisa está en un grupo de WhatsApp del barrio donde se comparten ofertas de empleo y cursos. Algunas personas envían mensajes repetidos y cadenas que nadie ha verificado.",
                 pasos=[
                     P("💬", "Abra WhatsApp y reconozca sus chats y sus contactos.",
                       "Guarde los contactos con un nombre que pueda reconocer, por ejemplo: Rosa vecina."),
                     P("✍️", "Escriba mensajes claros y respetuosos.",
                       "Escribir todo en MAYÚSCULAS se entiende como si estuviera gritando."),
                     P("📎", "Envíe fotos y documentos con el clip 📎.",
                       "Antes de enviar, revise que sea el archivo correcto y el chat correcto."),
                     P("👥", "Use los grupos para organizar actividades de la comunidad y del estudio.",
                       "Respete las normas y los horarios del grupo."),
                     P("🛡️", "Revise la privacidad en Ajustes y verifique la información antes de reenviarla.",
                       "Nunca comparta el código de 6 números que le llega por mensaje: con ese código otra persona se queda con su WhatsApp."),
                 ],
                 glosario=[("Mensajería instantánea", "Mensajes que llegan en el momento, como en WhatsApp."),
                           ("Grupo", "Chat entre varias personas."),
                           ("Reenviado", "Mensaje que otra persona escribió y que le pasaron. Si dice Reenviado muchas veces, ha circulado mucho."),
                           ("Privacidad", "Control sobre quién ve su foto, su estado y sus datos."),
                           ("Código de verificación", "Número que llega por mensaje para confirmar que la cuenta es suya. Es secreto.")],
                 recuerde=["La comunicación digital también exige respeto.",
                           "No todo lo que llega es verdad: verifique antes de reenviar.",
                           "El código de verificación de WhatsApp no se le da a nadie."]),
             dict(
                 titulo="Videollamadas y reuniones virtuales",
                 para_que="Para participar en clases, entrevistas, capacitaciones y reuniones a distancia.",
                 situacion="Pedro pasó a la entrevista de un empleo y es virtual. Le enviaron un enlace de Google Meet, pero no sabe cómo entrar ni cómo prender el micrófono y la cámara.",
                 pasos=[
                     P("📲", "Instale o abra la aplicación de la reunión, por ejemplo Google Meet o Zoom.",
                       "Revise antes que tiene buena conexión a internet y batería suficiente."),
                     P("🔗", "Toque el enlace de la invitación.",
                       "Confirme que el enlace llegó de quien lo invitó y no de un desconocido."),
                     P("🎙️", "Pruebe el micrófono y el sonido antes de entrar.",
                       "Con audífonos se escucha mejor y se oye menos ruido."),
                     P("📹", "Prenda o apague la cámara según le indiquen. El ícono tachado significa apagado.",
                       "Busque un lugar tranquilo y con luz de frente, no detrás de usted."),
                     P("👋", "Entre a tiempo y respete los turnos para hablar.",
                       "Silencie su micrófono cuando no esté hablando."),
                 ],
                 glosario=[("Videollamada", "Llamada con audio y video por internet."),
                           ("Micrófono", "Lo que capta su voz."),
                           ("Cámara", "Lo que capta su imagen."),
                           ("Enlace", "Dirección que se toca para entrar a la reunión."),
                           ("Silenciar", "Apagar el micrófono por un momento.")],
                 recuerde=["Pruebe el audio antes de entrar.",
                           "Silencie el micrófono mientras otros hablan.",
                           "No comparta con desconocidos los enlaces de reuniones privadas."]),
             dict(
                 titulo="Hojas de cálculo para organizar información",
                 dispositivo="computador",
                 para_que="Para llevar cuentas, presupuestos y listas, y hacer sumas y promedios sin errores.",
                 situacion="Una asociación de vendedores de Valledupar anota sus ventas en un cuaderno y hace las cuentas a mano. Cada semana se equivocan y no saben cuánto vendieron de verdad.",
                 pasos=[
                     P("📊", "Abra Excel o Google Sheets.",
                       "Google Sheets es gratuito y funciona en el navegador y en el celular."),
                     P("🧾", "Reconozca las filas (números), las columnas (letras) y las celdas.",
                       "Cada celda se nombra con su letra y su número, por ejemplo B3."),
                     P("✍️", "Escriba los títulos en la primera fila: Fecha, Producto, Cantidad y Precio. Debajo, un dato por celda.",
                       "Escriba los precios solo con números, sin el signo $ ni puntos, para poder sumarlos."),
                     P("➗", "Haga cálculos con fórmulas como =SUMA(B2:B7) o =PROMEDIO(B2:B7).",
                       "Toda fórmula empieza con el signo igual (=). Los dos puntos indican desde qué celda hasta cuál."),
                     P("📈", "Seleccione los datos y cree un gráfico para ver los resultados.",
                       "Revise que los datos estén completos antes de sacar conclusiones del gráfico."),
                 ],
                 glosario=[("Celda", "Cada cuadrito de la hoja donde va un dato."),
                           ("Fila", "Línea horizontal de celdas, identificada con un número."),
                           ("Columna", "Línea vertical de celdas, identificada con una letra."),
                           ("Fórmula", "Operación que hace el cálculo por usted. Empieza con =."),
                           ("Gráfico", "Dibujo que muestra los datos.")],
                 recuerde=["Las hojas de cálculo ordenan la información.",
                           "Las fórmulas hacen las cuentas sin errores.",
                           "Los gráficos ayudan a entender los resultados."]),
             dict(
                 titulo="Presentaciones digitales",
                 dispositivo="computador",
                 para_que="Para explicar ideas con diapositivas en exposiciones, proyectos, capacitaciones y emprendimientos.",
                 situacion="Un grupo de jóvenes tiene que presentar su idea de negocio ante una organización comunitaria. Necesitan mostrarla de forma ordenada y visual.",
                 pasos=[
                     P("🎨", "Abra PowerPoint, Canva o Google Slides.",
                       "Canva y Google Slides son gratuitos y funcionan en el celular."),
                     P("🧩", "Organice las diapositivas en inicio, desarrollo y cierre.",
                       "Escriba primero en una hoja los temas que quiere contar."),
                     P("🔤", "Use títulos claros y textos cortos.",
                       "Una buena regla: una idea por diapositiva y pocas palabras."),
                     P("🖼️", "Agregue imágenes y gráficos que tengan que ver con el tema.",
                       "Use imágenes propias o de bancos gratuitos que permitan usarlas."),
                     P("🎤", "Ensaye la exposición y revise el orden de las diapositivas.",
                       "No lea la diapositiva: explique con sus palabras."),
                 ],
                 glosario=[("Diapositiva", "Cada página de una presentación."),
                           ("Plantilla", "Diseño ya hecho que se puede usar."),
                           ("Transición", "Efecto al pasar de una diapositiva a otra."),
                           ("Infografía", "Imagen que explica información con dibujos y pocos textos."),
                           ("Exposición", "Presentación hablada de un tema ante un público.")],
                 recuerde=["Una presentación debe comunicar ideas claras.",
                           "Las imágenes deben apoyar el mensaje, no distraer.",
                           "Ensayar mejora la exposición."]),
             dict(
                 titulo="Almacenamiento en la nube y trabajo en equipo",
                 para_que="Para guardar archivos en internet, abrirlos desde cualquier equipo y trabajar con otras personas en el mismo documento.",
                 situacion="Un grupo de estudiantes hace un proyecto. Cada uno tiene una versión distinta del documento y ya no saben cuál es la última.",
                 pasos=[
                     P("☁️", "Conozca servicios de nube como Google Drive, OneDrive o Dropbox.",
                       "Si tiene cuenta de Gmail, ya tiene Google Drive con espacio gratuito."),
                     P("🔐", "Entre con su cuenta y proteja el acceso.",
                       "Use una contraseña segura y active la verificación en dos pasos."),
                     P("📤", "Suba sus documentos y cree carpetas para ordenarlos.",
                       "Ponga nombres claros a los archivos para que el equipo los encuentre."),
                     P("🔗", "Comparta el documento con su equipo y elija el permiso: Lector, Comentarista o Editor.",
                       "Lector solo ve; Comentarista puede dejar notas; Editor puede cambiar el contenido."),
                     P("🤝", "Trabajen en el mismo documento y revisen el historial de cambios.",
                       "No dé permiso de edición a personas que no conoce."),
                 ],
                 glosario=[("Nube", "Servicio en internet donde se guardan archivos."),
                           ("Sincronización", "Que el archivo se actualice igual en todos sus equipos."),
                           ("Compartir", "Dar acceso a un archivo a otras personas."),
                           ("Permiso", "Lo que otra persona puede hacer con su archivo: ver, comentar o editar."),
                           ("Historial de versiones", "Registro de los cambios, que permite volver a una versión anterior.")],
                 recuerde=["La nube le permite abrir sus archivos desde cualquier lugar.",
                           "Los permisos controlan quién puede cambiar un documento.",
                           "Proteja su cuenta: ahí están todos sus archivos."]),
         ]),
    # =====================================================================
    dict(titulo="Seguridad y ciudadanía digital", icono="🛡️", nivel_bloom="Comprender y analizar",
         descripcion="Proteja su información y desenvuélvase con responsabilidad en internet.",
         lecciones=[
             dict(
                 titulo="Contraseñas seguras",
                 para_que="Para proteger su correo, sus redes sociales, su banco y sus demás cuentas.",
                 situacion="A Marta le robaron su cuenta de Facebook. Usaba la misma contraseña en todas sus cuentas y era su nombre con el año en que nació.",
                 pasos=[
                     P("🔐", "Haga una lista de las cuentas que debe proteger.",
                       "Empiece por el correo: con él se recuperan casi todas las demás cuentas."),
                     P("🧠", "Cree contraseñas largas y difíciles de adivinar.",
                       "Una buena idea es unir tres o cuatro palabras al azar con un número, por ejemplo: Mango-Bicicleta-Lluvia-27."),
                     P("🔄", "Use una contraseña distinta para cada servicio.",
                       "Si roban una, las demás cuentas siguen protegidas."),
                     P("📱", "Active la verificación en dos pasos donde se pueda.",
                       "Así, además de la contraseña, se pide un código que llega a su celular."),
                     P("🛡️", "Guarde sus contraseñas en un gestor de contraseñas o en un lugar privado.",
                       "No las escriba en papeles a la vista ni las envíe por mensaje."),
                 ],
                 glosario=[("Contraseña", "Clave secreta para entrar a una cuenta."),
                           ("Autenticación", "Comprobar que usted es quien dice ser."),
                           ("Verificación en dos pasos", "Pedir un segundo código, además de la contraseña, para entrar."),
                           ("Gestor de contraseñas", "Aplicación que guarda sus claves de forma protegida."),
                           ("Ciberseguridad", "Protección de las cuentas, los equipos y los datos.")],
                 recuerde=["Las contraseñas deben ser largas y distintas en cada cuenta.",
                           "La verificación en dos pasos agrega una capa de protección.",
                           "Nunca comparta sus claves."]),
             dict(
                 titulo="Cómo reconocer estafas y mensajes falsos",
                 para_que="Para reconocer intentos de fraude, suplantación y robo de datos antes de caer en ellos.",
                 situacion="A Julián le llega un mensaje que parece de su banco: dice que su cuenta será bloqueada hoy y que debe entrar a un enlace para actualizar sus datos.",
                 pasos=[
                     P("🚨", "Desconfíe de los mensajes que dan miedo, meten prisa o prometen premios inesperados.",
                       "Los estafadores presionan para que usted actúe sin pensar."),
                     P("🔍", "Revise quién envía el mensaje y mire bien la dirección del enlace.",
                       "Una dirección parecida a la del banco, con palabras de más o letras cambiadas, es falsa."),
                     P("🚫", "Nunca entregue contraseñas, códigos de verificación ni datos de tarjetas desde un enlace que le llegó.",
                       "Ningún banco le pide su clave ni sus códigos por mensaje o por llamada."),
                     P("🏦", "Si tiene dudas, comuníquese con la entidad por sus canales oficiales.",
                       "Busque usted mismo el teléfono o la aplicación oficial; no use los del mensaje."),
                     P("📢", "Reporte y bloquee el mensaje.",
                       "Si ya entregó datos de su banco, llame de inmediato a su banco para bloquear sus productos."),
                 ],
                 glosario=[("Phishing", "Engaño con mensajes o páginas falsas para robar datos o claves."),
                           ("Suplantación", "Hacerse pasar por otra persona o entidad."),
                           ("Fraude digital", "Estafa hecha por internet, mensajes o llamadas."),
                           ("Enlace", "Dirección que lleva a una página. Puede ser falsa aunque parezca real."),
                           ("Canal oficial", "Teléfono, página o aplicación verdaderos de una entidad.")],
                 recuerde=["Desconfíe de los mensajes que exigen actuar ya.",
                           "Nunca entregue códigos ni claves por un enlace.",
                           "Verifique siempre por los canales oficiales."]),
             dict(
                 titulo="Protección de datos personales",
                 para_que="Para saber qué información suya debe cuidar y cómo controlar lo que publica en internet.",
                 situacion="Daniela publica en redes sociales fotos de su familia, de sus documentos y de su casa. No sabe que personas desconocidas pueden usar esa información.",
                 pasos=[
                     P("👤", "Identifique cuáles son sus datos personales: nombre completo, número de cédula, dirección, teléfono y ubicación.",
                       "No todo se debe publicar. Su cédula, por ejemplo, permite que alguien se haga pasar por usted."),
                     P("⚙️", "Revise la privacidad de sus redes sociales.",
                       "Elija que solo sus amigos vean sus publicaciones."),
                     P("📷", "Piense antes de publicar fotos o documentos.",
                       "Mire el fondo de la foto: una dirección, una placa o un documento pueden aparecer sin que lo note."),
                     P("🔒", "No entregue sus datos en formularios o páginas que no conoce.",
                       "Pregúntese quién pide los datos, para qué y si de verdad los necesita."),
                     P("🧾", "Conozca sus derechos sobre sus datos en Colombia.",
                       "La Ley 1581 de 2012 los protege. La Superintendencia de Industria y Comercio (SIC) recibe las quejas."),
                 ],
                 glosario=[("Dato personal", "Información que lo identifica o permite identificarlo."),
                           ("Privacidad digital", "Control sobre lo que comparte en internet."),
                           ("Huella digital", "El rastro que deja todo lo que hace y publica en internet."),
                           ("Tratamiento de datos", "Recoger, guardar y usar información de las personas."),
                           ("Autorización", "Su permiso para que una entidad use sus datos.")],
                 recuerde=["Sus datos personales valen: cuídelos.",
                           "Configure la privacidad de sus cuentas.",
                           "Piense antes de publicar fotos o documentos."]),
             dict(
                 titulo="Noticias falsas y desinformación",
                 para_que="Para identificar información falsa o engañosa y no ayudar a que se riegue.",
                 situacion="En un grupo de WhatsApp de Valledupar circula una noticia que anuncia un subsidio de dinero para todas las familias. Muchos la comparten, pero nadie sabe de dónde salió.",
                 pasos=[
                     P("📰", "Lea la noticia completa antes de compartirla.",
                       "El titular puede exagerar o decir algo distinto al contenido."),
                     P("🔎", "Fíjese quién la publicó y de qué fuente sale.",
                       "Desconfíe de publicaciones sin autor ni entidad responsable."),
                     P("📅", "Revise la fecha y el contexto.",
                       "Una noticia vieja puede circular como si fuera de hoy."),
                     P("🔍", "Compare con otros medios y con la página oficial de la entidad.",
                       "Si es un anuncio de la Alcaldía o del Gobierno, debe estar en su página oficial."),
                     P("🚫", "No comparta lo que no pudo verificar. Si encuentra la información correcta, compártala.",
                       "Así ayuda a frenar la desinformación en su comunidad."),
                 ],
                 glosario=[("Desinformación", "Información falsa o engañosa que se riega como si fuera verdad."),
                           ("Verificar", "Comprobar si una información es cierta."),
                           ("Fuente", "De dónde sale una noticia o un dato."),
                           ("Titular", "La frase principal de una noticia."),
                           ("Contexto", "Las circunstancias, como la fecha y el lugar, que ayudan a entender una información.")],
                 recuerde=["No comparta noticias sin verificarlas.",
                           "Revise la fecha y el origen.",
                           "Los anuncios oficiales están en las páginas oficiales."]),
             dict(
                 titulo="Trámites y servicios digitales en Colombia",
                 para_que="Para usar las páginas oficiales del Estado y hacer consultas y trámites sin desplazarse.",
                 situacion="A doña Rosa le cuesta ir hasta una oficina para hacer un trámite. Quiere aprender a consultarlo y hacerlo desde su celular.",
                 pasos=[
                     P("🇨🇴", "Busque la página oficial de la entidad. El portal GOV.CO reúne los trámites del Estado.",
                       "Verifique que la dirección termine en .gov.co."),
                     P("🔎", "Busque el trámite y lea los requisitos.",
                       "Revise si necesita documentos, si tiene costo y cuánto se demora."),
                     P("📝", "Llene el formulario con datos verdaderos y actualizados.",
                       "Revise todo antes de enviar; un error puede hacer que le rechacen la solicitud."),
                     P("📥", "Descargue y guarde el comprobante o el número de radicado.",
                       "Tómele una captura de pantalla y guárdela en un lugar seguro."),
                     P("📲", "Consulte en qué va su trámite por los canales oficiales.",
                       "No le pague a intermediarios que prometen hacerlo más rápido."),
                 ],
                 glosario=[("Gobierno digital", "Servicios del Estado que se hacen por internet."),
                           ("Trámite", "Pasos para obtener un servicio o una respuesta de una entidad."),
                           ("Radicado", "Número que identifica su solicitud."),
                           ("Portal oficial", "Página verdadera de una entidad."),
                           ("Certificado digital", "Documento electrónico que se descarga y demuestra algo, como estar afiliado.")],
                 recuerde=["Use solo páginas oficiales.",
                           "Guarde el comprobante o el radicado.",
                           "No pague a intermediarios desconocidos."]),
         ]),
    # =====================================================================
    dict(titulo="Tecnología para el empleo y el emprendimiento", icono="💼", nivel_bloom="Aplicar y analizar",
         descripcion="Aproveche la tecnología para buscar empleo, estudiar y hacer crecer su negocio.",
         lecciones=[
             dict(
                 titulo="Búsqueda de empleo por internet",
                 para_que="Para encontrar ofertas de trabajo, revisar convocatorias y postularse por internet.",
                 situacion="Miguel busca empleo en Valledupar. Ha oído que hay páginas con ofertas de trabajo, pero no sabe usarlas ni distinguir cuáles ofertas son confiables.",
                 pasos=[
                     P("💼", "Conozca los portales de empleo: el Servicio Público de Empleo, la Agencia Pública de Empleo del SENA y otras plataformas reconocidas.",
                       "Entre siempre por la dirección oficial del portal."),
                     P("🔎", "Busque con palabras sobre lo que sabe hacer, por ejemplo: auxiliar de bodega Valledupar.",
                       "Incluya el cargo, sus habilidades y la ciudad."),
                     P("📍", "Use los filtros de ciudad, modalidad, salario y experiencia.",
                       "Los filtros muestran solo las ofertas que cumplen esas condiciones."),
                     P("📄", "Lea los requisitos y prepare su hoja de vida para cada oferta.",
                       "No ponga información falsa sobre su experiencia."),
                     P("📤", "Postúlese por el canal que indica la oferta y haga seguimiento.",
                       "Desconfíe de las ofertas que le cobran dinero para contratarlo."),
                 ],
                 glosario=[("Vacante", "Puesto de trabajo disponible."),
                           ("Postulación", "Solicitud para participar en un proceso de selección."),
                           ("Perfil laboral", "Resumen de lo que sabe hacer y de su experiencia."),
                           ("Portal de empleo", "Página que une a empresas y personas que buscan trabajo."),
                           ("Teletrabajo", "Trabajo que se hace desde la casa usando internet.")],
                 recuerde=["Use portales de empleo confiables.",
                           "Ajuste su postulación a cada oferta.",
                           "Una empresa seria no cobra por contratarlo."]),
             dict(
                 titulo="Mi hoja de vida digital",
                 para_que="Para hacer un documento que presente bien su formación, su experiencia y sus habilidades.",
                 situacion="Laura terminó el bachillerato y quiere su primer empleo. Nunca ha tenido un trabajo formal y cree que por eso no puede hacer una hoja de vida.",
                 pasos=[
                     P("📄", "Abra un procesador de texto o una plantilla de hoja de vida.",
                       "Puede usar Word, Google Docs o Canva."),
                     P("👤", "Ponga sus datos de contacto: nombre, celular, correo y ciudad.",
                       "No incluya datos que no se necesitan, como su número de cuenta bancaria."),
                     P("🎓", "Anote sus estudios, cursos y certificados.",
                       "Ordénelos del más reciente al más antiguo."),
                     P("⭐", "Describa sus habilidades, proyectos y experiencias, incluso las que no fueron pagadas.",
                       "Un voluntariado o una práctica también muestran responsabilidad y lo que sabe hacer."),
                     P("📥", "Revise la ortografía y guárdela en PDF con un nombre claro, como Hoja_de_vida_Laura.pdf.",
                       "Pídale a alguien de confianza que la lea antes de enviarla."),
                 ],
                 glosario=[("Hoja de vida", "Documento que resume su perfil para un empleo."),
                           ("Experiencia", "Trabajos y actividades que ha realizado."),
                           ("Competencias", "Lo que sabe y lo que sabe hacer."),
                           ("Certificado", "Documento que demuestra que terminó un curso o una formación."),
                           ("Perfil", "Párrafo corto al inicio que dice quién es y qué busca.")],
                 recuerde=["La hoja de vida debe ser clara y verdadera.",
                           "Los cursos y los voluntariados también cuentan.",
                           "Revísela antes de enviarla."]),
             dict(
                 titulo="Marketing digital para pequeños negocios",
                 para_que="Para dar a conocer sus productos en internet, llegar a más clientes y fortalecer su negocio.",
                 situacion="Una emprendedora de Valledupar hace postres en su casa. Son muy buenos, pero poca gente conoce su negocio. Quiere promocionarlos en redes sociales.",
                 pasos=[
                     P("🛍️", "Defina qué productos va a promocionar y a quiénes les quiere vender.",
                       "Piense qué necesidad resuelve: cumpleaños, reuniones, antojos."),
                     P("📸", "Tome fotos claras y bonitas de sus productos.",
                       "Use luz natural, cerca de una ventana, y un fondo sencillo."),
                     P("📱", "Cree un perfil de negocio, por ejemplo WhatsApp Business o una página de empresa.",
                       "Separe lo del negocio de su vida personal."),
                     P("📝", "Publique con descripción, precio y forma de hacer el pedido.",
                       "La información debe ser clara y verdadera."),
                     P("📊", "Revise qué publicaciones reciben más comentarios y mensajes.",
                       "Use esos resultados para decidir qué publicar después."),
                 ],
                 glosario=[("Marketing digital", "Dar a conocer y vender productos por internet."),
                           ("Emprendimiento", "Negocio o idea que alguien pone en marcha."),
                           ("Público objetivo", "Las personas con más probabilidad de comprarle."),
                           ("Interacción", "Comentarios, reacciones y mensajes que recibe una publicación."),
                           ("Alcance", "Cuántas personas vieron una publicación.")],
                 recuerde=["Sepa a quién le quiere vender.",
                           "Publique fotos e información de calidad.",
                           "Mire los resultados para mejorar."]),
             dict(
                 titulo="Inteligencia artificial en la vida diaria",
                 para_que="Para usar herramientas de inteligencia artificial que le ayuden a aprender, organizarse y tener ideas, con precaución.",
                 situacion="Sebastián tiene que preparar una exposición para un curso comunitario. Ha oído hablar de la inteligencia artificial, pero no sabe cómo usarla ni qué cuidados debe tener.",
                 pasos=[
                     P("🤖", "Conozca herramientas de inteligencia artificial como ChatGPT, Gemini o Copilot.",
                       "Lea sus condiciones de uso; algunas tienen versión gratuita."),
                     P("💬", "Escriba instrucciones claras: qué necesita, para qué y cómo quiere la respuesta.",
                       "Ejemplo: explícame en 5 puntos sencillos cómo ahorrar agua, para una charla de 10 minutos."),
                     P("🎯", "Úsela para tener ideas, explicaciones o borradores.",
                       "Pídale ejemplos de su barrio o su ciudad para que la respuesta le sirva más."),
                     P("🔎", "Compruebe la información en fuentes confiables.",
                       "La inteligencia artificial se equivoca y a veces inventa datos que suenan ciertos."),
                     P("🔐", "Proteja su información y use los resultados con responsabilidad.",
                       "No escriba contraseñas, números de documentos ni datos privados."),
                 ],
                 glosario=[("Inteligencia artificial", "Programas que pueden hacer tareas como escribir, resumir o responder preguntas."),
                           ("Prompt o instrucción", "Lo que usted le escribe a la herramienta para pedirle algo."),
                           ("Modelo", "El sistema entrenado que genera las respuestas."),
                           ("Automatización", "Que una máquina haga una tarea por usted."),
                           ("Sesgo", "Inclinación o error que hace que una respuesta no sea justa ni completa.")],
                 recuerde=["La IA ayuda, pero no reemplaza su criterio.",
                           "Verifique siempre lo que responde.",
                           "No comparta datos privados con estas herramientas."]),
             dict(
                 titulo="Educación virtual y aprendizaje autónomo",
                 para_que="Para aprovechar cursos y recursos gratuitos en internet y mejorar sus oportunidades.",
                 situacion="Camila quiere estudiar desde su casa porque no siempre puede ir a un centro de formación. Encuentra cursos gratuitos en internet, pero no sabe cómo organizarse para terminarlos.",
                 pasos=[
                     P("🎓", "Conozca plataformas de formación como SENA Sofia Plus, Colombia Aprende, Coursera o edX.",
                       "Revise cuáles cursos son gratuitos o tienen becas."),
                     P("🔎", "Elija un curso que tenga que ver con sus intereses o con el trabajo que busca.",
                       "Mire el contenido, la duración y los requisitos antes de inscribirse."),
                     P("📅", "Defina un horario de estudio y una meta para cada semana.",
                       "Mejor ratos cortos todos los días que muchas horas un solo día."),
                     P("💻", "Haga las actividades, revise los materiales y presente las evaluaciones.",
                       "Tome apuntes y pregunte en los foros cuando tenga dudas."),
                     P("🏅", "Termine el curso y descargue el certificado si lo ofrecen.",
                       "Guarde los certificados y agréguelos a su hoja de vida."),
                 ],
                 glosario=[("Educación virtual", "Aprender por internet."),
                           ("Plataforma educativa", "Página donde están los cursos y sus materiales."),
                           ("Curso virtual", "Formación que se hace por internet."),
                           ("Aprendizaje autónomo", "Organizar y dirigir uno mismo su aprendizaje."),
                           ("Certificado", "Documento que demuestra que terminó un curso.")],
                 recuerde=["En internet hay muchas oportunidades para aprender.",
                           "La constancia vale más que las jornadas largas.",
                           "Los certificados fortalecen su hoja de vida."]),
         ]),
]

DIAGNOSTICO = [  # (texto, índice del módulo)
    ("¿Sabe prender un computador y abrir un programa?", 0),
    ("¿Sabe crear una carpeta y guardar un archivo en ella?", 0),
    ("¿Sabe enviar un correo con un archivo adjunto?", 0),
    ("¿Sabe entrar a una videollamada desde un enlace?", 1),
    ("¿Sabe hacer una suma en una hoja de cálculo como Excel?", 1),
    ("¿Sabe compartir un archivo desde Google Drive u otra nube?", 1),
    ("¿Sabe reconocer un mensaje falso que pide datos o dinero?", 2),
    ("¿Sabe activar la verificación en dos pasos en una cuenta?", 2),
    ("¿Sabe buscar ofertas de empleo por internet?", 3),
    ("¿Sabe hacer su hoja de vida en el computador o en el celular?", 3),
]

USUARIOS_PRUEBA = [  # nombre, celular, PIN, rol
    ("Administrador", "3000000001", "1234", "administrador"),
    ("Facilitador de prueba", "3000000002", "1234", "facilitador"),
    ("María Pérez (aprendiz demo)", "3000000003", "1234", "aprendiz"),
]


def _j(x) -> str:
    return json.dumps(x, ensure_ascii=False)


def sembrar(db: Session) -> bool:
    if db.scalar(select(Modulo.id).limit(1)):
        return False
    modulos = []
    azar = random.Random(2026)   # semilla fija: mismo orden en cada instalación
    for i, m in enumerate(CONTENIDO, start=1):
        mod = Modulo(orden=i, titulo=m["titulo"], icono=m["icono"],
                     descripcion=m["descripcion"], nivel_bloom=m["nivel_bloom"])
        for j, l in enumerate(m["lecciones"], start=1):
            lec = Leccion(orden=j, titulo=l["titulo"], para_que=l["para_que"], situacion=l["situacion"],
                          pasos=_j(l["pasos"]),
                          glosario=_j([{"termino": t, "definicion": d} for t, d in l["glosario"]]),
                          recuerde=_j(l["recuerde"]), dispositivo=l.get("dispositivo", "celular"))
            for k, q in enumerate(PREGUNTAS[l["titulo"]], start=1):
                act = Actividad(orden=k, pregunta=q["pregunta"], explicacion=q["explicacion"],
                                nivel_bloom=q["bloom"])
                opciones = list(q["opciones"])
                azar.shuffle(opciones)   # la correcta no queda siempre en la misma posición
                act.opciones = [Opcion(texto=t, correcta=ok, retroalimentacion=r)
                                for t, ok, r in opciones]
                lec.actividades.append(act)
            mod.lecciones.append(lec)
        db.add(mod)
        modulos.append(mod)
    db.flush()
    for k, (texto, idx) in enumerate(DIAGNOSTICO, start=1):
        db.add(PreguntaDiagnostico(orden=k, texto=texto, modulo_id=modulos[idx].id))
    usuarios = {}
    admin_cel, admin_pin = os.getenv("ADMIN_CELULAR", "").strip(), os.getenv("ADMIN_PIN", "").strip()
    if admin_cel and admin_pin:
        # Despliegue público: no se crean los usuarios de prueba (sus PIN están en el README);
        # solo un administrador con el celular y el PIN definidos en las variables de entorno.
        if not re.fullmatch(r"3\d{9}", admin_cel) or not re.fullmatch(r"\d{4}", admin_pin) or pin_trivial(admin_pin):
            raise SystemExit("ADMIN_CELULAR debe tener 10 dígitos y empezar por 3; ADMIN_PIN, 4 dígitos no triviales.")
        db.add(Usuario(nombre="Administrador", celular=admin_cel, pin_hash=hash_pin(admin_pin), rol="administrador"))
        db.flush()
        db.add(Grupo(nombre="Grupo piloto"))
        db.commit()
        return True
    for nombre, cel, pin, rol in USUARIOS_PRUEBA:
        u = Usuario(nombre=nombre, celular=cel, pin_hash=hash_pin(pin), rol=rol)
        db.add(u)
        usuarios[rol] = u
    db.flush()
    g = Grupo(nombre="Grupo piloto", facilitador_id=usuarios["facilitador"].id)
    db.add(g)
    db.flush()
    usuarios["aprendiz"].grupo_id = g.id
    db.commit()
    return True


if __name__ == "__main__":
    from . import models  # noqa: F401
    from .database import Base, SessionLocal, engine
    if "--reiniciar" in sys.argv:
        Base.metadata.drop_all(engine)
        print("Base de datos reiniciada.")
    Base.metadata.create_all(engine)
    with SessionLocal() as s:
        print("Datos iniciales cargados." if sembrar(s) else "La base ya tenía datos (use --reiniciar para reemplazarlos).")
