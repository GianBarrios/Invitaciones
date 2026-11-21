"""Videos verticales (1080x1920) de "un año de migración", un ave por video.

Estilo: mapa oscuro a pantalla completa, enjambre de aves simuladas con estela,
ruta resaltada de un ejemplar, dial de meses con kilómetros, capítulos por temporada.

Uso:  python3 generar.py [clave ...]          (sin argumentos: todas las aves de aves.py)
      python3 generar.py colibri --preview    (solo 4 fotogramas PNG de prueba)
"""
import json, math, os, subprocess, sys, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from aves import AVES

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "videos")
W, H, FPS = 1080, 1920, 30
INTRO, YEAR, HOLD, OUTRO = 1.5, 36.0, 1.5, 3.5      # segundos
DUR = INTRO + YEAR + HOLD + OUTRO
N_BIRDS = 420

FD = "/usr/share/fonts/opentype/inter/"
def font(w, s, disp=False):
    return ImageFont.truetype(FD + ("InterDisplay-" if disp else "Inter-") + f"{w}.otf", s)

OCEAN, LAND, EDGE = (17, 19, 22), (44, 48, 50), (78, 84, 86)
WHITE, MUTED, DIM = (240, 240, 236), (168, 170, 168), (120, 122, 120)
GOLD, ORANGE, SPARK = (238, 190, 110), (247, 160, 64), (255, 236, 190)
MESES = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]
INICIAL = "EFMAMJJASOND"


# ---------------- geografía ----------------
def decode_topojson(path, mesh=False):
    tj = json.load(open(path))
    sc, tr = tj["transform"]["scale"], tj["transform"]["translate"]
    arcs = []
    for arc in tj["arcs"]:
        x = y = 0; pts = []
        for dx, dy in arc:
            x += dx; y += dy
            pts.append((x * sc[0] + tr[0], y * sc[1] + tr[1]))
        arcs.append(pts)
    if mesh:
        return arcs
    def ring(ids):
        out = []
        for i in ids:
            a = arcs[i] if i >= 0 else arcs[~i][::-1]
            out.extend(a if not out else a[1:])
        return out
    polys = []
    for obj in tj["objects"].values():
        geoms = obj["geometries"] if obj["type"] == "GeometryCollection" else [obj]
        for g in geoms:
            if g["type"] == "Polygon":
                polys.append([ring(r) for r in g["arcs"]])
            elif g["type"] == "MultiPolygon":
                polys.extend([[ring(r) for r in p] for p in g["arcs"]])
    return polys


class Proj:
    """Equirectangular con corrección cos(lat) para que el mapa no se vea estirado."""
    def __init__(self, lat_top, lat_bot, lon_c):
        self.k = H / (lat_top - lat_bot)
        self.lat_top, self.lon_c = lat_top, lon_c
        self.c = math.cos(math.radians((lat_top + lat_bot) / 2))
        half = W / 2 / (self.k * self.c)
        self.lon0, self.lon1, self.lat_bot = lon_c - half, lon_c + half, lat_bot

    def __call__(self, lon, lat):
        lon, lat = np.asarray(lon, float), np.asarray(lat, float)
        return (lon - self.lon_c) * self.c * self.k + W / 2, (self.lat_top - lat) * self.k


def render_map(pr, polys, borders):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.path import Path
    from matplotlib.patches import PathPatch
    hexc = lambda c: "#%02x%02x%02x" % c
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off()
    ax.set_xlim(pr.lon0, pr.lon1); ax.set_ylim(pr.lat_bot, pr.lat_top)
    fig.patch.set_facecolor(hexc(OCEAN))
    for shift in (-360, 0, 360):
        for poly in polys:
            verts, codes = [], []
            for r in poly:
                if len(r) < 3: continue
                if np.abs(np.diff([x for x, _ in r])).max() > 180:   # anillo que cruza el antimeridiano
                    xs = np.degrees(np.unwrap(np.radians([x for x, _ in r])))
                    r = list(zip(xs, [y for _, y in r]))
                verts += [(x + shift, y) for x, y in r]
                codes += [Path.MOVETO] + [Path.LINETO] * (len(r) - 1)
            if verts:
                ax.add_patch(PathPatch(Path(verts, codes), fc=hexc(LAND), ec=hexc(EDGE), lw=0.9))
        for arc in borders:
            a = np.array(arc)
            cut = np.where(np.abs(np.diff(a[:, 0])) > 180)[0] + 1   # no unir tramos que cruzan el antimeridiano
            for part in np.split(a, cut):
                if len(part) > 1 and np.abs(part[:, 1]).max() < 89:
                    ax.plot(part[:, 0] + shift, part[:, 1], color="#ffffff", alpha=0.07, lw=0.7)
    fig.canvas.draw()
    img = np.asarray(fig.canvas.buffer_rgba())[:, :, :3].astype(np.float32)
    plt.close(fig)

    # textura de relieve falsa + viñeta para dar profundidad
    rng = np.random.default_rng(7)
    noise = Image.fromarray((rng.random((H // 4, W // 4)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
    noise = np.asarray(noise.filter(ImageFilter.GaussianBlur(3)), np.float32) / 255
    is_land = (img.mean(axis=2) > 30)[:, :, None]
    img = img * np.where(is_land, 0.85 + 0.3 * noise[:, :, None], 1.0)
    yy, xx = np.mgrid[0:H, 0:W]
    vig = 1 - 0.55 * (((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2)
    img = img * np.clip(vig, 0.35, 1)[:, :, None]
    scrim = 1 - 0.45 * np.clip(1 - yy / 680, 0, 1) ** 1.5 - 0.4 * np.clip((yy - 1250) / 400, 0, 1) ** 1.5
    img = img * scrim[:, :, None]
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


# ---------------- rutas y simulación ----------------
def catmull(points, n=40):
    p = np.array(points, float)
    p = np.vstack([p[0], p, p[-1]])
    out = []
    for i in range(1, len(p) - 2):
        a, b, c, d = p[i - 1], p[i], p[i + 1], p[i + 2]
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * (2 * b + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t * t
                              + (-a + 3 * b - 3 * c + d) * t ** 3))
    out.append(p[-2])
    return np.array(out)


def resample(pts, n=1500):
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)]); s /= s[-1]
    u = np.linspace(0, 1, n)
    return np.column_stack([np.interp(u, s, pts[:, 0]), np.interp(u, s, pts[:, 1])])


def hav(lon1, lat1, lon2, lat2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


class Sim:
    def __init__(self, ave, pr):
        self.pr = pr
        self.legs = [resample(catmull(l)) for l in (ave["ida"], ave["vuelta"])]   # lon/lat
        self.legs_px = [np.column_stack(pr(l[:, 0], l[:, 1])) for l in self.legs]
        # agenda: (mes, u). u en [0,1] = ida (cría -> invernada), [1,2] = vuelta. Se desenrolla para que sea monótona.
        M, U = [], []
        for m, u in ave["agenda"]:
            if isinstance(u, (str, tuple)):        # nombre de lugar, o (nombre, tramo)
                name, leg = (u, ave["lugares"][u][2]) if isinstance(u, str) else u
                u = self.u_at(*ave["lugares"][name][:2], leg=leg)
            M.append(m); U.append(u)
        U = np.array(U, float)
        for i in range(1, len(U)):
            while U[i] < U[i - 1] - 1e-9: U[i] += 2
        self.M, self.U = np.array(M, float), U

        rng = np.random.default_rng(42)
        n = N_BIRDS
        self.delay = np.clip(rng.normal(0, ave.get("dispersion_meses", 0.45), n), -1.1, 1.1)
        self.delay[0] = 0
        def ellipse(spec):
            (clon, clat), (rlon, rlat) = spec
            r, a = np.sqrt(rng.random(n)), rng.random(n) * 2 * np.pi
            lon, lat = clon + rlon * r * np.cos(a), clat + rlat * r * np.sin(a)
            x, y = pr(lon, lat)
            return np.column_stack([x, y])
        b0, w0 = self.legs_px[0][0], self.legs_px[0][-1]
        self.offB = ellipse(ave["zona_cria"]) - b0
        self.offW = ellipse(ave["zona_invernada"]) - w0
        self.offB[0] = self.offW[0] = 0
        self.jit = rng.normal(0, 10, (n, 2)); self.jit[0] = 0
        self.phase = rng.random(n) * 6.28
        self.bright = 0.45 + 0.55 * rng.random(n)

        # ejemplar destacado: recorrido acumulado en km
        mm = np.linspace(0, 12, 4000)
        lonlat = self.lonlat(self.u(mm))
        d = np.concatenate([[0], np.cumsum(hav(lonlat[:-1, 0], lonlat[:-1, 1], lonlat[1:, 0], lonlat[1:, 1]))])
        if ave.get("km_anuales"):
            d = d / d[-1] * ave["km_anuales"]
        self.hero_m, self.hero_km = mm, d
        self.hero_px = np.column_stack(pr(lonlat[:, 0], lonlat[:, 1]))

    def u_at(self, lon, lat, leg):
        l = self.legs[leg]
        i = np.argmin((l[:, 0] - lon) ** 2 + (l[:, 1] - lat) ** 2)
        return leg + i / (len(l) - 1)

    def u(self, m):
        return np.interp(np.mod(m, 12), self.M, self.U) % 2

    def _on_leg(self, u, legs):
        idx = np.minimum(u, 1.999999)
        leg = (idx >= 1).astype(int)
        s = idx - leg
        n = len(legs[0]) - 1
        i = np.clip((s * n).astype(int), 0, n - 1)
        f = (s * n - i)[:, None]
        out = np.empty((len(u), 2))
        for L in (0, 1):
            k = leg == L
            out[k] = legs[L][i[k]] * (1 - f[k]) + legs[L][i[k] + 1] * f[k]
        return out, leg, s

    def lonlat(self, u):
        return self._on_leg(np.atleast_1d(u), self.legs)[0]

    def positions(self, m, t):
        u = self.u(m - self.delay)
        base, leg, s = self._on_leg(u, self.legs_px)
        w = np.where(leg == 0, s, 1 - s)               # 0 = zona de cría, 1 = invernada
        spread = 1 - 0.85 * np.sin(np.pi * w)          # se concentran en mitad de la ruta
        off = (self.offB * (1 - w)[:, None] + self.offW * w[:, None]) * spread[:, None]
        wob = 5 * np.column_stack([np.sin(t * 0.9 + self.phase), np.cos(t * 0.7 + self.phase * 1.3)])
        return base + off + self.jit * (0.4 + 0.6 * spread[:, None]) + wob


# ---------------- dibujo ----------------
def ease(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def fmt(n): return f"{int(round(n)):,}".replace(",", " ")


def text(d, xy, s, f, col, a=1.0, anchor="la", shadow=True):
    if a <= 0: return
    if shadow:
        d.text((xy[0] + 2, xy[1] + 3), s, font=f, fill=(0, 0, 0, int(160 * a)), anchor=anchor)
    d.text(xy, s, font=f, fill=col + (int(255 * a),), anchor=anchor)


def draw_dial(d, cx, cy, m, km, caption, a):
    R = 92
    d.ellipse([cx - R - 22, cy - R - 22, cx + R + 22, cy + R + 22], fill=(12, 13, 15, int(150 * a)))
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=(90, 90, 88, int(255 * a)), width=5)
    end = -90 + 360 * (m / 12)
    if m > 0.01:
        steps = max(2, int(m * 8))
        for i in range(steps):           # arco con degradado
            a0 = -90 + 360 * (m / 12) * i / steps
            a1 = -90 + 360 * (m / 12) * (i + 1) / steps
            k = i / steps
            col = tuple(int(ORANGE[j] * (1 - k) + SPARK[j] * k) for j in range(3))
            d.arc([cx - R, cy - R, cx + R, cy + R], a0, a1 + 0.6, fill=col + (int(255 * a),), width=7)
    f = font("SemiBold", 17)
    for i, ch in enumerate(INICIAL):
        ang = math.radians(-90 + 360 * (i + 0.5) / 12)
        text(d, (cx + (R - 24) * math.cos(ang), cy + (R - 24) * math.sin(ang)), ch, f, MUTED, a, "mm", False)
    ang = math.radians(end)
    kx, ky = cx + R * math.cos(ang), cy + R * math.sin(ang)
    d.ellipse([kx - 10, ky - 10, kx + 10, ky + 10], fill=(255, 255, 255, int(255 * a)))
    text(d, (cx, cy - 8), MESES[int(m) % 12], font("Bold", 46), WHITE, a, "mm", False)
    if km > 0.5:
        text(d, (cx, cy + 30), f"{fmt(km)} km", font("SemiBold", 21), GOLD, a, "mm", False)
    text(d, (cx, cy + R + 50), caption, font("SemiBold", 25), GOLD, a, "mm")


def make(key, polys, borders, preview=False):
    ave = AVES[key]
    pr = Proj(*ave["mapa"])
    base = render_map(pr, polys, borders).convert("RGBA")
    sim = Sim(ave, pr)

    # lugares: punto + etiqueta fija
    places = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(places)
    fpl = font("SemiBold", 27)
    for name, (lon, lat, _leg, *lado) in ave["lugares"].items():
        x, y = pr(lon, lat)
        x, y = float(x), float(y)
        pd.ellipse([x - 7, y - 7, x + 7, y + 7], fill=WHITE + (255,))
        right = not lado or lado[0] != "izq"
        text(pd, (x + 16 if right else x - 16, y), name, fpl, WHITE, 1, "lm" if right else "rm")
    base = Image.alpha_composite(base, places)

    f_title, f_sub = font("Bold", 66, True), font("Medium", 29)
    f_ch, f_chs = font("Bold", 42, True), font("Medium", 29)
    f_name, f_sci, f_meta = font("Bold", 54, True), font("Regular", 33), font("Medium", 23)
    f_leg, f_src = font("Medium", 25), font("Medium", 20)

    tmp = os.path.join(OUT, f".frames_{key}")
    shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp, exist_ok=True)
    n_frames = int(DUR * FPS)
    frames = [int(n_frames * x) for x in (0.12, 0.35, 0.55, 0.8)] if preview else range(n_frames)

    for fi in frames:
        t = fi / FPS
        m = min(max((t - INTRO) / YEAR * 12, 0), 11.999)
        a_in = ease(t / 0.8)
        frame = base.copy()

        # --- enjambre con estelas ---
        sw = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sd = ImageDraw.Draw(sw)
        tails = [sim.positions(m - k * 0.035, t - k * 0.05) for k in range(7)]
        for k in range(6, 0, -1):
            p0, p1 = tails[k], tails[k - 1]
            al = (0.55 * (1 - k / 7)) * sim.bright
            for i in range(N_BIRDS):
                if abs(p0[i, 0] - p1[i, 0]) + abs(p0[i, 1] - p1[i, 1]) < 0.6: continue
                sd.line([tuple(p0[i]), tuple(p1[i])], fill=GOLD + (int(255 * al[i] * a_in),), width=2)
        head = tails[0]
        for i in range(1, N_BIRDS):
            x, y = head[i]; r = 2.6
            sd.ellipse([x - r, y - r, x + r, y + r], fill=SPARK + (int(255 * sim.bright[i] * a_in),))
        glow = sw.filter(ImageFilter.GaussianBlur(5))
        frame = Image.alpha_composite(frame, glow)
        frame = Image.alpha_composite(frame, glow)
        frame = Image.alpha_composite(frame, sw)

        # --- ruta del ejemplar destacado ---
        k = int(np.searchsorted(sim.hero_m, m))
        if k > 2:
            hl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            hd = ImageDraw.Draw(hl)
            pts = [tuple(p) for p in sim.hero_px[:k:3]] + [tuple(sim.hero_px[k - 1])]
            hd.line(pts, fill=ORANGE + (255,), width=10, joint="curve")
            frame = Image.alpha_composite(frame, hl.filter(ImageFilter.GaussianBlur(10)))
            hl2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(hl2).line(pts, fill=(255, 205, 130, 255), width=4, joint="curve")
            frame = Image.alpha_composite(frame, hl2)
        hx, hy = sim.hero_px[max(k - 1, 0)]
        d = ImageDraw.Draw(frame)
        pulse = 0.5 + 0.5 * math.sin(t * 4)
        rr = 14 + 6 * pulse
        d.ellipse([hx - rr, hy - rr, hx + rr, hy + rr], outline=ORANGE + (int(200 * a_in),), width=3)
        d.ellipse([hx - 8, hy - 8, hx + 8, hy + 8], fill=(255, 220, 160, int(255 * a_in)))

        # --- textos ---
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        y = 200
        for ln in ave["titulo"]:
            text(d, (60, y), ln, f_title, WHITE, a_in); y += 74
        text(d, (60, y + 10), ave["subtitulo"], f_sub, MUTED, a_in)

        cap = ""
        for (m0, m1, tit, sub, c) in ave["capitulos"]:
            a_on = 1.0 if m0 == 0 else ease((m - m0) / 0.25)
            a_off = 1.0 if m1 >= 12 else 1 - ease((m - (m1 - 0.25)) / 0.25)
            a = a_on * a_off * a_in
            if a > 0:
                text(d, (60, 460), tit, f_ch, WHITE, a)
                yy = 515
                for ln in sub:
                    text(d, (60, yy), ln, f_chs, (210, 210, 205), a); yy += 38
            if m0 <= m < m1: cap = c
        draw_dial(d, 905, 300, m, float(np.interp(m, sim.hero_m, sim.hero_km)), cap, a_in)

        # bloque de especie (abajo a la izquierda)
        text(d, (60, 1300), ave["nombre"], f_name, WHITE, a_in)
        text(d, (60, 1366), ave["cientifico"], f_sci, MUTED, a_in)
        text(d, (60, 1412), ave["ficha"], f_meta, DIM, a_in)
        # leyenda (abajo a la derecha)
        lx = W - 60
        text(d, (lx - 40, 1385), "Aves simuladas", f_leg, (215, 215, 210), a_in, "rm")
        d.ellipse([lx - 18, 1376, lx, 1394], fill=SPARK + (int(255 * a_in),))
        text(d, (lx - 40, 1425), "Ruta de un ejemplar", f_leg, (215, 215, 210), a_in, "rm")
        d.line([lx - 26, 1425, lx, 1425], fill=ORANGE + (int(255 * a_in),), width=5)
        text(d, (60, 1500), ave["firma"], f_src, DIM, a_in, shadow=False)
        text(d, (W - 60, 1500), ave["fuentes"], f_src, DIM, a_in, "ra", shadow=False)
        frame = Image.alpha_composite(frame, ov)

        # --- cierre ---
        te = t - (INTRO + YEAR + HOLD)
        if te > 0:
            ae = ease(te / 0.6)
            frame = Image.alpha_composite(frame, Image.new("RGBA", (W, H), (8, 9, 11, int(215 * ae))))
            d = ImageDraw.Draw(frame)
            y = 780
            for ln in ave["cierre"]:
                text(d, (W / 2, y), ln, font("Bold", 64, True), WHITE, ae, "ma"); y += 80
            text(d, (W / 2, y + 40), "Sígueme para ver más migraciones", font("SemiBold", 36), GOLD, ae, "ma")

        out_png = os.path.join(tmp, f"{fi:05d}.png")
        frame.convert("RGB").save(out_png, compress_level=1)

    if preview:
        print("preview en", tmp); return
    out = os.path.join(OUT, f"{ave['archivo']}.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(tmp, "%05d.png"),
                    "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-shortest",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-preset", "medium",
                    "-c:a", "aac", "-movflags", "+faststart", out], check=True)
    shutil.rmtree(tmp)
    print("listo:", out)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    polys = decode_topojson(os.path.join(HERE, "land-50m.json"))
    borders = decode_topojson(os.path.join(HERE, "countries-50m.json"), mesh=True)
    for k in (args or list(AVES)):
        make(k, polys, borders, preview="--preview" in sys.argv)
