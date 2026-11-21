"""Datos de cada ave (un video por ave). Para añadir otra, copia un bloque y ajústalo.

mapa:     (latitud superior, latitud inferior, longitud central) del encuadre vertical.
ida:      ruta zona de cría -> zona de invernada, puntos (lon, lat).
vuelta:   ruta zona de invernada -> zona de cría.
zona_*:   ((lon, lat) centro, (radio_lon, radio_lat)) donde se reparten las aves simuladas.
lugares:  nombre -> (lon, lat, tramo 0=ida 1=vuelta[, "izq" para poner la etiqueta a la izquierda]).
agenda:   (mes, posición). Mes 0 = 1 de enero, 12 = 31 de diciembre.
          Posición: 0 = zona de cría, 1 = zona de invernada, 2 = de vuelta en la zona de cría
          (luego 3 = invernada otra vez...). También vale el nombre de un lugar o (nombre, tramo).
capitulos: (mes_inicio, mes_fin, título, [líneas], texto bajo el dial)
km_anuales: si se indica, el contador del dial se escala a esa cifra documentada.
"""

AVES = {
    "colibri": dict(
        archivo="01_colibri_garganta_rubi",
        titulo=["Un año de migración", "del colibrí"],
        subtitulo="Rutas aproximadas según fechas típicas de migración",
        nombre="Colibrí garganta rubí",
        cientifico="Archilochus colubris",
        ficha="≈3 g · 7–9 cm · 53 aleteos por segundo",
        firma="",
        fuentes="Fuentes: Cornell Lab · Audubon · Natural Earth",
        mapa=(77.9, -27.9, -85),
        zona_cria=((-84, 40), (12, 6.5)),
        zona_invernada=((-90, 16), (7, 3.5)),
        ida=[(-83, 40), (-88, 35.5), (-95, 29.8), (-97.4, 26), (-97.2, 22), (-94, 18.4), (-90, 16)],
        vuelta=[(-90, 16), (-89.6, 21.3), (-90, 25), (-90.2, 29.3), (-87, 34.5), (-83, 40)],
        lugares={
            "Yucatán": (-89.6, 21.3, 1),
            "Luisiana": (-90.2, 29.3, 1),
            "Costa de Texas": (-97.4, 26, 0, "izq"),
        },
        agenda=[(0, 1), (2.2, 1), (2.9, "Yucatán"), (3.0, "Yucatán"), (3.07, "Luisiana"),
                (4.5, 2), (7.8, 2), (9.3, "Costa de Texas"), (10.4, 3), (12, 3)],
        capitulos=[
            (0, 2.2, "Invierno en el trópico", ["Pasan el invierno entre el sur", "de México y Centroamérica"], "Invernada"),
            (2.2, 3.8, "Un salto sobre el mar", ["Cruzan ~800 km del Golfo de México", "sin parar, en unas 20 horas"], "Rumbo al norte"),
            (3.8, 7.6, "Temporada de cría", ["Anidan en el este de Norteamérica,", "hasta el sur de Canadá"], "Cría"),
            (7.6, 9.0, "Combustible para el viaje", ["Casi duplican su peso en grasa", "antes de partir"], "Preparación"),
            (9.0, 12, "De vuelta al sur", ["Muchos regresan bordeando", "la costa de Texas"], "Rumbo al sur"),
        ],
        cierre=["3 gramos.", "800 km sobre el mar."],
    ),

    "playero": dict(
        archivo="02_playero_rojizo",
        titulo=["Un año de migración", "del playero rojizo"],
        subtitulo="Rutas aproximadas según fechas típicas de migración",
        nombre="Playero rojizo",
        cientifico="Calidris canutus rufa",
        ficha="≈130 g · ~30 000 km al año · especie amenazada",
        firma="",
        fuentes="Fuentes: USFWS · Manomet · Natural Earth",
        mapa=(176.3, -170.3, -79.8),
        km_anuales=30000,
        zona_cria=((-92, 68), (16, 3.5)),
        zona_invernada=((-69, -53), (2.5, 1.2)),
        ida=[(-90, 67.5), (-84, 58), (-80, 52), (-70, 46), (-62, 38), (-52, 20), (-44.5, -1.5),
             (-38, -10), (-46, -26), (-56, -37), (-64, -42), (-67, -48), (-69, -53)],
        vuelta=[(-69, -53), (-67, -48), (-65, -41), (-58, -36), (-51, -31.2), (-41, -20), (-38, -9),
                (-44.5, -1.5), (-56, 13), (-68, 29), (-75, 39), (-80, 48), (-86, 58), (-90, 67.5)],
        lugares={
            "Tierra del Fuego": (-69, -53, 1),
            "Lagoa do Peixe": (-51, -31.2, 1),
            "Maranhão": (-44.5, -1.5, 1),
            "Bahía de Delaware": (-75, 39, 1),
            "Bahía de James": (-80, 52, 0),
        },
        agenda=[(0, 1), (2.0, 1), (3.1, "Lagoa do Peixe"), (3.8, "Lagoa do Peixe"), (4.3, "Maranhão"),
                (4.4, "Maranhão"), (4.6, "Bahía de Delaware"), (5.1, "Bahía de Delaware"), (5.45, 2),
                (7.0, 2), (7.4, "Bahía de James"), (7.9, "Bahía de James"), (8.3, ("Maranhão", 0)),
                (9.2, ("Maranhão", 0)), (10.5, 3), (12, 3)],
        capitulos=[
            (0, 2.0, "Verano en el fin del mundo", ["Pasan el verano austral", "en Tierra del Fuego"], "Invernada"),
            (2.0, 4.4, "Rumbo al norte", ["Suben por la costa", "de Argentina y Brasil"], "Rumbo al norte"),
            (4.4, 5.4, "El festín de Delaware", ["Casi duplican su peso comiendo", "huevos de cangrejo herradura"], "Parada clave"),
            (5.4, 7.2, "Cría en el Ártico", ["Anidan en la tundra", "del Ártico canadiense"], "Cría"),
            (7.2, 10.5, "El gran salto al sur", ["Cruzan el Atlántico sin parar", "hasta el norte de Brasil"], "Rumbo al sur"),
            (10.5, 12, "Más lejos que la Luna", ["Un ejemplar, «B95», voló en su vida", "más que la distancia a la Luna"], "De regreso"),
        ],
        cierre=["30 000 km al año.", "Y cada vez quedan menos."],
    ),

    "charran": dict(
        archivo="03_charran_artico",
        titulo=["Un año de migración", "del charrán ártico"],
        subtitulo="Rutas aproximadas según fechas típicas de migración",
        nombre="Charrán ártico",
        cientifico="Sterna paradisaea",
        ficha="≈100 g · vive 30+ años · 70 900 km al año",
        firma="",
        fuentes="Fuentes: Egevang et al. 2010 (PNAS) · Natural Earth",
        mapa=(187.7, -198.6, -20),
        km_anuales=70900,
        zona_cria=((-18, 72), (26, 6)),
        zona_invernada=((-25, -68), (30, 3)),
        ida=[(-22, 72), (-32, 60), (-36, 48), (-26, 35), (-20, 20), (-17, 5), (-5, -12), (6, -30),
             (5, -48), (-12, -63), (-25, -68)],
        vuelta=[(-25, -68), (-10, -55), (0, -38), (-12, -15), (-28, 5), (-42, 25), (-44, 42), (-36, 56), (-22, 72)],
        lugares={
            "Groenlandia": (-42, 64, 0, "izq"),
            "Atlántico Norte": (-36, 48, 0, "izq"),
            "Antártida": (-25, -68, 1),
        },
        agenda=[(0, 1), (3.4, 1), (4.8, 2), (7.3, 2), (7.7, "Atlántico Norte"), (8.6, "Atlántico Norte"),
                (10.9, 3), (12, 3)],
        capitulos=[
            (0, 3.4, "Verano en la Antártida", ["Pescan entre el hielo", "del mar de Weddell"], "Verano austral"),
            (3.4, 4.9, "Regreso en forma de S", ["Siguen los vientos y vuelven", "al norte en unos 40 días"], "Rumbo al norte"),
            (4.9, 7.3, "Cría en el Ártico", ["Anidan en Groenlandia, Islandia", "y el norte de Europa"], "Verano ártico"),
            (7.3, 8.7, "Parada en alta mar", ["Recargan energía varias semanas", "en el Atlántico Norte"], "Parada"),
            (8.7, 11.0, "Hacia el sur", ["Bajan por el Atlántico", "rumbo a la Antártida"], "Rumbo al sur"),
            (11.0, 12, "Dos veranos al año", ["Ningún animal ve tanta", "luz solar como él"], "Llegada"),
        ],
        cierre=["70 900 km en un año.", "Pesa 100 gramos."],
    ),
}
