import flet as ft

def main(page: ft.Page):
    page.title = "Geotecnia App V3.2"
    page.scroll = "adaptive"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 450
    page.window_height = 800

    # ==========================================
    # INTERFAZ GRÁFICA (INPUTS)
    # ==========================================

    sis_dropdown = ft.Dropdown(
        label="Sistema de Salida",
        options=[
            ft.dropdown.Option("1", "SI (kN, m3)"),
            ft.dropdown.Option("2", "Métrico (g, cm3)"),
            ft.dropdown.Option("3", "Inglés (lb, ft3)"),
        ],
        value="1",
        width=300
    )

    gw_input    = ft.TextField(label="gw (Peso esp. agua) [Dejar vacío para default]", width=300)
    emax_input  = ft.TextField(label="e max (def 0.91)", width=145)
    emin_input  = ft.TextField(label="e min (def 0.35)", width=145)

    vars_info = [
        ("W",        "Peso tot"),     ("Ws",       "Peso sol"),
        ("Ww",       "Peso agua"),    ("V",        "Vol tot"),
        ("Vs",       "Vol sol"),      ("Vv",       "Vol vacios"),
        ("Vw",       "Vol agua"),     ("Va",       "Vol aire"),
        ("Gs",       "Grav esp"),     ("w",        "Humedad %"),
        ("e",        "Rel vacios"),   ("n",        "Porosidad %"),
        ("Sr",       "Saturac %"),    ("gamma",    "g humedo"),
        ("gammad",   "g seco"),       ("gammasat", "g saturado"),
        ("gammas",   "g solidos"),    ("Cr",       "Compacid %"),
    ]

    inputs_dict = {}
    inputs_col  = ft.Column(spacing=10)

    for v, desc in vars_info:
        txt_field = ft.TextField(label=f"{v} ({desc})", width=300, dense=True)
        inputs_dict[v] = txt_field
        inputs_col.controls.append(txt_field)

    resultados_texto  = ft.Text(size=16, weight="bold")
    paso_a_paso_texto = ft.Text(size=14, selectable=True)
    diagrama_col      = ft.Column(spacing=0)

    def toggle_paso_a_paso(e):
        paso_a_paso_texto.visible = not paso_a_paso_texto.visible
        page.update()

    # ==========================================
    # MOTOR DE CÁLCULO
    # ==========================================
    def ejecutar_calculo(e):
        resultados_texto.value  = ""
        paso_a_paso_texto.value = ""
        diagrama_col.controls.clear()

        sis = sis_dropdown.value

        if sis == '2':
            u_f, u_v, u_g, def_gw = "g",  "cm3", "g/cm3",   1.0
        elif sis == '3':
            u_f, u_v, u_g, def_gw = "lb", "ft3", "lb/ft3",  62.428
        else:
            u_f, u_v, u_g, def_gw = "kN", "m3",  "kN/m3",   9.806
            sis = '1'

        try:
            gw_in = gw_input.value.replace(',', '.')
            gw = float(gw_in) if gw_in.strip() != "" else def_gw
        except ValueError:
            gw = def_gw

        try:
            emax_in = emax_input.value.replace(',', '.')
            emax = float(emax_in) if emax_in.strip() != "" else 0.91
        except ValueError:
            emax = 0.91

        try:
            emin_in = emin_input.value.replace(',', '.')
            emin = float(emin_in) if emin_in.strip() != "" else 0.35
        except ValueError:
            emin = 0.35

        d = {}
        for v, _ in vars_info:
            val_in = inputs_dict[v].value.replace(',', '.')
            if val_in.strip() != "":
                try:
                    val = float(val_in)
                    d[v] = val / 100.0 if v in ["w", "n", "Sr", "Cr"] else val
                except ValueError:
                    pass

        d["gw"]   = gw
        d["emax"] = emax
        d["emin"] = emin

        # ==========================================
        # REGLAS FÍSICAS
        # ==========================================
        reglas = [
            ("Ww",       ["W","Ws"],                    "W - Ws",              "{:.3f}-{:.3f}",                     lambda c: c["W"]-c["Ws"],                                     u_f),
            ("Ws",       ["W","Ww"],                    "W - Ww",              "{:.3f}-{:.3f}",                     lambda c: c["W"]-c["Ww"],                                     u_f),
            ("W",        ["Ws","Ww"],                   "Ws + Ww",             "{:.3f}+{:.3f}",                     lambda c: c["Ws"]+c["Ww"],                                    u_f),
            ("Ww",       ["w","Ws"],                    "w * Ws",              "{:.3f}*{:.3f}",                     lambda c: c["w"]*c["Ws"],                                     u_f),
            ("Ws",       ["Ww","w"],                    "Ww / w",              "{:.3f}/{:.3f}",                     lambda c: c["Ww"]/c["w"],                                     u_f),
            ("Ws",       ["W","w"],                     "W / (1+w)",           "{:.3f}/(1+{:.3f})",                 lambda c: c["W"]/(1+c["w"]),                                  u_f),
            ("W",        ["Ws","w"],                    "Ws * (1+w)",          "{:.3f}*(1+{:.3f})",                 lambda c: c["Ws"]*(1+c["w"]),                                 u_f),
            ("Ww",       ["Vw","gw"],                   "Vw * gw",             "{:.3f}*{:.3f}",                     lambda c: c["Vw"]*c["gw"],                                    u_f),
            ("Vv",       ["V","Vs"],                    "V - Vs",              "{:.3f}-{:.3f}",                     lambda c: c["V"]-c["Vs"],                                     u_v),
            ("Vs",       ["V","Vv"],                    "V - Vv",              "{:.3f}-{:.3f}",                     lambda c: c["V"]-c["Vv"],                                     u_v),
            ("V",        ["Vs","Vv"],                   "Vs + Vv",             "{:.3f}+{:.3f}",                     lambda c: c["Vs"]+c["Vv"],                                    u_v),
            ("Vw",       ["Ww","gw"],                   "Ww / gw",             "{:.3f}/{:.3f}",                     lambda c: c["Ww"]/c["gw"],                                    u_v),
            ("Va",       ["Vv","Vw"],                   "Vv - Vw",             "{:.3f}-{:.3f}",                     lambda c: c["Vv"]-c["Vw"],                                    u_v),
            ("Vv",       ["Va","Vw"],                   "Va + Vw",             "{:.3f}+{:.3f}",                     lambda c: c["Va"]+c["Vw"],                                    u_v),
            ("Vw",       ["Vv","Va"],                   "Vv - Va",             "{:.3f}-{:.3f}",                     lambda c: c["Vv"]-c["Va"],                                    u_v),
            ("Vw",       ["Sr","Vv"],                   "Sr * Vv",             "{:.3f}*{:.3f}",                     lambda c: c["Sr"]*c["Vv"],                                    u_v),
            ("V",        ["W","gamma"],                 "W / g",               "{:.3f}/{:.3f}",                     lambda c: c["W"]/c["gamma"],                                  u_v),
            ("W",        ["V","gamma"],                 "V * g",               "{:.3f}*{:.3f}",                     lambda c: c["V"]*c["gamma"],                                  u_f),
            ("V",        ["Ws","gammad"],               "Ws / gd",             "{:.3f}/{:.3f}",                     lambda c: c["Ws"]/c["gammad"],                                u_v),
            ("Ws",       ["V","gammad"],                "V * gd",              "{:.3f}*{:.3f}",                     lambda c: c["V"]*c["gammad"],                                 u_f),
            ("Vs",       ["Ws","Gs","gw"],              "Ws/(Gs*gw)",          "{:.3f}/({:.3f}*{:.3f})",            lambda c: c["Ws"]/(c["Gs"]*c["gw"]),                          u_v),
            ("Ws",       ["Vs","Gs","gw"],              "Vs*Gs*gw",            "{:.3f}*{:.3f}*{:.3f}",              lambda c: c["Vs"]*c["Gs"]*c["gw"],                            u_f),
            ("e",        ["Vv","Vs"],                   "Vv / Vs",             "{:.3f}/{:.3f}",                     lambda c: c["Vv"]/c["Vs"],                                    "adim"),
            ("Vv",       ["e","Vs"],                    "e * Vs",              "{:.3f}*{:.3f}",                     lambda c: c["e"]*c["Vs"],                                     u_v),
            ("Vs",       ["Vv","e"],                    "Vv / e",              "{:.3f}/{:.3f}",                     lambda c: c["Vv"]/c["e"],                                     u_v),
            ("n",        ["Vv","V"],                    "Vv / V",              "{:.3f}/{:.3f}",                     lambda c: c["Vv"]/c["V"],                                     "dec"),
            ("e",        ["n","n"],                     "n / (1-n)",           "{:.3f}/(1-{:.3f})",                 lambda c: c["n"]/(1-c["n"]),                                  "adim"),
            ("n",        ["e","e"],                     "e / (1+e)",           "{:.3f}/(1+{:.3f})",                 lambda c: c["e"]/(1+c["e"]),                                  "dec"),
            ("Cr",       ["emax","e","emax","emin"],    "(emax-e)/(emax-emin)","({:.3f}-{:.3f})/({:.3f}-{:.3f})",  lambda c: (c["emax"]-c["e"])/(c["emax"]-c["emin"]),           "dec"),
            ("e",        ["emax","Cr","emax","emin"],   "emax-Cr*(emax-emin)", "{:.3f}-{:.3f}*({:.3f}-{:.3f})",    lambda c: c["emax"]-c["Cr"]*(c["emax"]-c["emin"]),            "adim"),
            ("gammas",   ["Ws","Vs"],                   "Ws / Vs",             "{:.3f}/{:.3f}",                     lambda c: c["Ws"]/c["Vs"],                                    u_g),
            ("Gs",       ["gammas","gw"],               "gs / gw",             "{:.3f}/{:.3f}",                     lambda c: c["gammas"]/c["gw"],                                "adim"),
            ("gammas",   ["Gs","gw"],                   "Gs * gw",             "{:.3f}*{:.3f}",                     lambda c: c["Gs"]*c["gw"],                                    u_g),
            ("w",        ["Ww","Ws"],                   "Ww / Ws",             "{:.3f}/{:.3f}",                     lambda c: c["Ww"]/c["Ws"],                                    "dec"),
            ("Sr",       ["Vw","Vv"],                   "Vw / Vv",             "{:.3f}/{:.3f}",                     lambda c: c["Vw"]/c["Vv"],                                    "dec"),
            ("Sr",       ["w","Gs","e"],                "(w*Gs)/e",            "({:.3f}*{:.3f})/{:.3f}",            lambda c: (c["w"]*c["Gs"])/c["e"],                            "dec"),
            ("w",        ["Sr","e","Gs"],               "(Sr*e)/Gs",           "({:.3f}*{:.3f})/{:.3f}",            lambda c: (c["Sr"]*c["e"])/c["Gs"],                           "dec"),
            ("Gs",       ["Sr","e","w"],                "(Sr*e)/w",            "({:.3f}*{:.3f})/{:.3f}",            lambda c: (c["Sr"]*c["e"])/c["w"],                            "adim"),
            ("e",        ["w","Gs","Sr"],               "(w*Gs)/Sr",           "({:.3f}*{:.3f})/{:.3f}",            lambda c: (c["w"]*c["Gs"])/c["Sr"],                           "adim"),
            ("Ar",       ["Va","Vv"],                   "Va / Vv",             "{:.3f}/{:.3f}",                     lambda c: c["Va"]/c["Vv"],                                    "dec"),
            ("gamma",    ["W","V"],                     "W / V",               "{:.3f}/{:.3f}",                     lambda c: c["W"]/c["V"],                                      u_g),
            ("gammad",   ["Ws","V"],                    "Ws / V",              "{:.3f}/{:.3f}",                     lambda c: c["Ws"]/c["V"],                                     u_g),
            ("gammad",   ["gamma","w"],                 "g / (1+w)",           "{:.3f}/(1+{:.3f})",                 lambda c: c["gamma"]/(1+c["w"]),                              u_g),
            ("gamma",    ["gammad","w"],                "gd * (1+w)",          "{:.3f}*(1+{:.3f})",                 lambda c: c["gammad"]*(1+c["w"]),                             u_g),
            ("gammad",   ["Gs","gw","e"],               "(Gs*gw)/(1+e)",       "({:.3f}*{:.3f})/(1+{:.3f})",        lambda c: (c["Gs"]*c["gw"])/(1+c["e"]),                       u_g),
            ("e",        ["Gs","gw","gammad"],          "(Gs*gw/gd)-1",        "({:.3f}*{:.3f}/{:.3f})-1",          lambda c: (c["Gs"]*c["gw"]/c["gammad"])-1,                    "adim"),
            ("gamma",    ["Gs","Sr","e","gw","e"],      "(Gs+Sr*e)*gw/(1+e)",  "({:.3f}+{:.3f}*{:.3f})*{:.3f}/(1+{:.3f})", lambda c: (c["Gs"]+c["Sr"]*c["e"])*c["gw"]/(1+c["e"]), u_g),
            ("Wsat",     ["Ws","Vv","gw"],              "Ws + Vv*gw",          "{:.3f}+{:.3f}*{:.3f}",              lambda c: c["Ws"]+(c["Vv"]*c["gw"]),                          u_f),
            ("gammasat", ["Wsat","V"],                  "Wsat / V",            "{:.3f}/{:.3f}",                     lambda c: c["Wsat"]/c["V"],                                   u_g),
            ("gammasat", ["Gs","e","gw","e"],           "(Gs+e)*gw/(1+e)",     "({:.3f}+{:.3f})*{:.3f}/(1+{:.3f})",lambda c: ((c["Gs"]+c["e"])*c["gw"])/(1+c["e"]),              u_g),
            ("e",        ["Gs","gw","gammasat","gammasat","gw"], "(Gs*gw-gsat)/(gsat-gw)", "({:.3f}*{:.3f}-{:.3f})/({:.3f}-{:.3f})", lambda c: (c["Gs"]*c["gw"]-c["gammasat"])/(c["gammasat"]-c["gw"]), "adim"),
            ("Gs",       ["gammasat","e","gw","e"],     "(gsat*(1+e)/gw)-e",   "({:.3f}*(1+{:.3f})/{:.3f})-{:.3f}",lambda c: (c["gammasat"]*(1+c["e"])/c["gw"])-c["e"],          "adim"),
            ("Wsat",     ["gammasat","V"],              "gsat * V",            "{:.3f}*{:.3f}",                     lambda c: c["gammasat"]*c["V"],                               u_f),
        ]

        # ==========================================
        # CICLO DE CÁLCULO Y PASO A PASO
        # ==========================================
        p = 1
        intentar = True
        asumido  = False
        registro_pasos = "[ PASO A PASO ]\n\n"

        while intentar:
            intentar = False
            for obj, reqs, form_txt, form_tpl, func, unid in reglas:
                if obj not in d and all(r in d for r in reqs):
                    try:
                        res = func(d)
                        d[obj] = res
                        intentar = True
                        u_p   = "%" if unid == "dec" else ("" if unid == "adim" else unid)
                        final = res * 100 if unid == "dec" else res
                        valores   = [d[r] for r in reqs]
                        sust_str  = form_tpl.format(*valores)
                        registro_pasos += f"{p}. {obj} = {form_txt}\n"
                        registro_pasos += f"   = {sust_str} = {final:.4f}{u_p}\n\n"
                        p += 1
                    except ZeroDivisionError:
                        pass

            if not intentar and not asumido:
                tiene_ext = any(k in d for k in ["V","Vs","Vv","Vw","Va","W","Ws","Ww"])
                if not tiene_ext and len(d) > 2:
                    registro_pasos += f"\n[!] Asumiendo Vs = 1.0 {u_v}\n"
                    d["Vs"]  = 1.0
                    asumido  = True
                    intentar = True

        paso_a_paso_texto.value = registro_pasos

        # ==========================================
        # FORMATEO DE RESULTADOS
        # ==========================================
        orden = [
            ("W",        "W total",  u_f), ("Ws",       "W sol",    u_f),
            ("Ww",       "W agua",   u_f), ("V",        "V total",  u_v),
            ("Vs",       "V sol",    u_v), ("Vv",       "V vacios", u_v),
            ("Vw",       "V agua",   u_v), ("Va",       "V aire",   u_v),
            ("e",        "Rel vac",  ""),  ("n",        "Porosid",  "%"),
            ("Sr",       "Saturac",  "%"), ("Ar",       "Aire",     "%"),
            ("w",        "Humedad",  "%"), ("Cr",       "Comp.Rel", "%"),
            ("gamma",    "g hum",    u_g), ("gammad",   "g sec",    u_g),
            ("gammasat", "g sat",    u_g), ("gammas",   "g sol",    u_g),
            ("Gs",       "Gs",       ""),
        ]

        texto_res = "RESULTADOS FINALES\n" + "="*30 + "\n"
        for v, nom, uni in orden:
            if v in d:
                if uni == "%":
                    texto_res += f"{nom:<9}: {d[v]*100:.3f} {uni}\n"
                else:
                    texto_res += f"{nom:<9}: {d[v]:.4f} {uni}\n"

        resultados_texto.value = texto_res

        # ==========================================
        # RENDERIZACIÓN DEL DIAGRAMA DE FASES
        # ==========================================
        va = d.get("Va", 0.0)
        vw = d.get("Vw", 0.0)
        vs = d.get("Vs", 0.0)
        ww = d.get("Ww", 0.0)
        ws = d.get("Ws", 0.0)

        # ✅ CORRECCIÓN 1: ft.Alignment(0,0) en lugar de ft.alignment.center
        # ✅ CORRECCIÓN 2: ft.Border(all sides) en lugar de ft.border.all()
        borde_negro = ft.Border(
            top    = ft.BorderSide(width=1, color="black"),
            bottom = ft.BorderSide(width=1, color="black"),
            left   = ft.BorderSide(width=1, color="black"),
            right  = ft.BorderSide(width=1, color="black"),
        )

        def crear_fase(vol_val, peso_val, color_hex, nombre):
            es_aire = color_hex == "#FFF176"
            return ft.Row(
                controls=[
                    ft.Text(
                        f"V={vol_val:.2f}{u_v}",
                        width=80,
                        text_align=ft.TextAlign.RIGHT
                    ),
                    ft.Container(
                        content=ft.Text(
                            nombre,
                            weight="bold",
                            color="black" if es_aire else "white"
                        ),
                        alignment=ft.Alignment(0, 0),   # ← CORRECCIÓN 1
                        width=100,
                        height=50,
                        bgcolor=color_hex,
                        border=borde_negro,              # ← CORRECCIÓN 2
                    ),
                    ft.Text(
                        f"W={peso_val:.2f}{u_f}",
                        width=80,
                        text_align=ft.TextAlign.LEFT
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10,
            )

        diagrama_col.controls.append(ft.Text("DIAGRAMA DE FASES", weight="bold"))

        if va > 0.0001:
            diagrama_col.controls.append(crear_fase(va, 0.0, "#FFF176", "AIRE"))
        if vw > 0.0001 or ww > 0.0001:
            diagrama_col.controls.append(crear_fase(vw, ww, "#42A5F5", "AGUA"))
        if vs > 0.0001 or ws > 0.0001:
            diagrama_col.controls.append(crear_fase(vs, ws, "#6D4C41", "SÓLIDO"))

        page.update()

    # ==========================================
    # CONSTRUCCIÓN DE LA PÁGINA
    # ==========================================
    page.add(
        ft.Text("RESOLVEDOR GEOTÉCNICO V3.2", size=20, weight="bold"),
        ft.Divider(),
        sis_dropdown,
        ft.Row([gw_input, emax_input, emin_input], wrap=True),
        ft.Text("DATOS (Dejar vacío para omitir):", weight="bold"),
        inputs_col,
        ft.ElevatedButton(
            "CALCULAR", on_click=ejecutar_calculo,
            width=300, bgcolor="blue", color="white"
        ),
        ft.Divider(),
        resultados_texto,
        diagrama_col,
        ft.ElevatedButton(
            "Ver / Ocultar Procedimiento",
            on_click=toggle_paso_a_paso,
            width=300
        ),
        paso_a_paso_texto,
    )

ft.app(target=main)
