# Tetris Terminal Edition
# Type-B: nivel y handicap seleccionables, 25 líneas,
# cinematicas estilo NES, leaderboards y estilos visuales.

import os,sys,time,random,json,tty,termios,select,signal

W,H=10,20
DATA=os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "tetris_data.json"
)

RESET="\033[0m"
BOLD="\033[1m"
DIM="\033[2m"

PIECES={
    "I":[[1,1,1,1]],
    "O":[[1,1],[1,1]],
    "T":[[0,1,0],[1,1,1]],
    "S":[[0,1,1],[1,1,0]],
    "Z":[[1,1,0],[0,1,1]],
    "J":[[1,0,0],[1,1,1]],
    "L":[[0,0,1],[1,1,1]]
}

DEFAULT={
    "scores":[
        {
            "name":"---",
            "score":0,
            "lines":0,
            "level":0
        }
        for _ in range(10)
    ],

    "typeb_scores":[
        {
            "name":"---",
            "score":0,
            "lines":25,
            "level":0,
            "height":0
        }
        for _ in range(10)
    ],

    "config":{
        "style":"NES",
        "ascii_palette":"MONO",
        "grid":True,
        "language":"ES"
    }
}

LANG={
    "ES":{
        "play":"JUGAR",
        "scores":"MEJORES PUNTUACIONES",
        "typeb_scores":"PUNTUACIONES TYPE-B",
        "config":"CONFIGURACIÓN",
        "instructions":"INSTRUCCIONES",
        "quit":"SALIR",
        "score":"PUNTOS",
        "lines":"LÍNEAS",
        "level":"NIVEL",
        "hold":"HOLD",
        "next":"SIGUIENTE",
        "gameover":"GAME OVER",
        "back":"VOLVER",
        "height":"HANDICAP / ALTURA",
        "difficulty":"DIFICULTAD",
        "name":"NOMBRE",
        "easy":"FÁCIL",
        "normal":"NORMAL",
        "hard":"DIFÍCIL"
    },

    "EN":{
        "play":"PLAY",
        "scores":"HIGH SCORES",
        "typeb_scores":"TYPE-B SCORES",
        "config":"SETTINGS",
        "instructions":"INSTRUCTIONS",
        "quit":"QUIT",
        "score":"SCORE",
        "lines":"LINES",
        "level":"LEVEL",
        "hold":"HOLD",
        "next":"NEXT",
        "gameover":"GAME OVER",
        "back":"BACK",
        "height":"HANDICAP / HEIGHT",
        "difficulty":"DIFFICULTY",
        "name":"NAME",
        "easy":"EASY",
        "normal":"NORMAL",
        "hard":"HARD"
    }
}


def load_data():

    try:

        with open(
            DATA,
            "r",
            encoding="utf-8"
        ) as f:

            d=json.load(f)

    except:

        d=json.loads(
            json.dumps(DEFAULT)
        )

    d.setdefault("scores",[])
    d.setdefault("typeb_scores",[])
    d.setdefault("config",{})

    d["config"].setdefault(
        "style",
        "NES"
    )

    d["config"].setdefault(
        "ascii_palette",
        "MONO"
    )

    d["config"].setdefault(
        "grid",
        True
    )

    d["config"].setdefault(
        "language",
        "ES"
    )

    for key in (
        "scores",
        "typeb_scores"
    ):

        for s in d[key]:

            s.setdefault(
                "name",
                "---"
            )

            s.setdefault(
                "score",
                0
            )

            s.setdefault(
                "lines",
                25 if key=="typeb_scores"
                else 0
            )

            s.setdefault(
                "level",
                0
            )

    while len(d["scores"])<10:

        d["scores"].append({
            "name":"---",
            "score":0,
            "lines":0,
            "level":0
        })

    while len(d["typeb_scores"])<10:

        d["typeb_scores"].append({
            "name":"---",
            "score":0,
            "lines":25,
            "level":0,
            "height":0
        })

    return d


data=load_data()
config=data["config"]


def save_data():

    with open(
        DATA,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )


def T(k):

    return LANG.get(
        config.get(
            "language",
            "ES"
        ),
        LANG["ES"]
    ).get(
        k,
        k
    )


def getkey():

    if not select.select(
        [sys.stdin],
        [],
        [],
        0
    )[0]:

        return None

    c=sys.stdin.read(1)

    if c=="\x1b":

        if not select.select(
            [sys.stdin],
            [],
            [],
            .01
        )[0]:

            return "esc"

        if sys.stdin.read(1)!="[":

            return "esc"

        if not select.select(
            [sys.stdin],
            [],
            [],
            .01
        )[0]:

            return "esc"

        return {
            "A":"up",
            "B":"down",
            "C":"right",
            "D":"left"
        }.get(
            sys.stdin.read(1)
        )

    return c.lower()


def newpiece(kind=None):

    if kind is None:

        kind=random.choice(
            list(PIECES)
        )

    shape=[
        r[:]
        for r in PIECES[kind]
    ]

    return {
        "kind":kind,
        "shape":shape,
        "x":W//2-len(shape[0])//2,
        "y":0
    }


def rotate(shape):

    return [
        list(r)
        for r in zip(
            *shape[::-1]
        )
    ]


board=[]
score=0
lines=0
level=0
hold=None
hold_used=False

difficulty="NORMAL"

game_mode="A"

typeb_target=25
typeb_height=0


def collide(
    p,
    x=None,
    y=None,
    shape=None
):

    x=p["x"] if x is None else x

    y=p["y"] if y is None else y

    shape=(
        p["shape"]
        if shape is None
        else shape
    )

    for py,row in enumerate(shape):

        for px,v in enumerate(row):

            if not v:
                continue

            bx=x+px
            by=y+py

            if bx<0 or bx>=W:
                return True

            if by>=H:
                return True

            if by>=0 and board[by][bx]:
                return True

    return False


def move(
    p,
    dx,
    dy
):

    if not collide(
        p,
        p["x"]+dx,
        p["y"]+dy
    ):

        p["x"]+=dx
        p["y"]+=dy

        return True

    return False


def rotate_piece(p):

    s=rotate(
        p["shape"]
    )

    for dx in (
        0,
        -1,
        1,
        -2,
        2
    ):

        if not collide(
            p,
            p["x"]+dx,
            p["y"],
            s
        ):

            p["x"]+=dx
            p["shape"]=s

            return


def hard_drop(p):

    while move(
        p,
        0,
        1
    ):

        pass


def ghost_y(p):

    y=p["y"]

    while not collide(
        p,
        p["x"],
        y+1
    ):

        y+=1

    return y


def lock_piece(p):

    global score

    for py,row in enumerate(
        p["shape"]
    ):

        for px,v in enumerate(row):

            if not v:
                continue

            x=p["x"]+px
            y=p["y"]+py

            if (
                0<=x<W
                and
                0<=y<H
            ):

                board[y][x]=p["kind"]

    score+=10


def completed():

    return [
        y
        for y in range(H)
        if all(board[y])
    ]


# ==========================================================
# ESTILOS
# ==========================================================

def nes_cell(k):

    # T / O / I:
    # azul oscuro con el detalle blanco
    # centrado dentro del bloque.

    if k in (
        "T",
        "O",
        "I"
    ):

        return (
            "\033[48;5;18m"
            "\033[97m"
            "█"
            "\033[0m"
            "\033[48;5;18m"
            "\033[97m"
            "█"
            "\033[0m"
        )

    # L / Z = azul oscuro

    if k in (
        "L",
        "Z"
    ):

        return (
            "\033[48;5;18m"
            "  "
            "\033[0m"
        )

    # S / J = azul claro

    return (
        "\033[48;5;39m"
        "  "
        "\033[0m"
    )


def atari_cell(k):

    colors={
        "T":"32",
        "I":"31",
        "O":"34",
        "Z":"36",
        "S":"33",
        "L":"93",
        "J":"35"
    }

    # O con hueco pequeño y cuadrado.

    if k=="O":

        return (
            "\033["+colors[k]+"m"
            "█"
            "\033[0m"
            "\033["+colors[k]+"m"
            "█"
            "\033[0m"
        )

    return (
        "\033["+colors[k]+"m"
        "██"
        "\033[0m"
    )


def pc_cell(k):

    colors={
        "I":"96",
        "O":"93",
        "T":"95",
        "S":"92",
        "Z":"91",
        "J":"94",
        "L":"33"
    }

    return (
        "\033["+colors[k]+"m"
        "██"
        "\033[0m"
    )


def ascii_cell(k):

    c={
        "CYAN":"96",
        "GREEN":"92",
        "WHITE":"97",
        "YELLOW":"93"
    }.get(
        config.get(
            "ascii_palette",
            "MONO"
        ),
        "97"
    )

    return (
        f"\033[{c}m"
        "[]"
        "\033[0m"
    )


def cell(k):

    s=config.get(
        "style",
        "NES"
    )

    if s=="NES":
        return nes_cell(k)

    if s=="ATARI ARCADE":
        return atari_cell(k)

    if s=="PC DOS":
        return pc_cell(k)

    if s=="ASCII":
        return ascii_cell(k)

    return (
        "\033[97m"
        "##"
        "\033[0m"
    )


def empty_cell():

    if config.get(
        "grid",
        True
    ):

        return "· "

    return "  "


def draw_field(temp):

    out=[
        "┌"+
        "──"*W+
        "┐"
    ]

    for y in range(H):

        line="│"

        for x in range(W):

            v=temp[y][x]

            if v is None:

                line+=empty_cell()

            elif v=="ghost":

                line+=(
                    DIM+
                    "░░"+
                    RESET
                )

            else:

                line+=cell(v)

        out.append(
            line+
            "│"
        )

    out.append(
        "└"+
        "──"*W+
        "┘"
    )

    return out


def make_board(p):

    temp=[
        r[:]
        for r in board
    ]

    gy=ghost_y(p)

    for py,row in enumerate(
        p["shape"]
    ):

        for px,v in enumerate(row):

            x=p["x"]+px
            y=gy+py

            if (
                v
                and
                0<=x<W
                and
                0<=y<H
                and
                temp[y][x] is None
            ):

                temp[y][x]="ghost"

    for py,row in enumerate(
        p["shape"]
    ):

        for px,v in enumerate(row):

            x=p["x"]+px
            y=p["y"]+py

            if (
                v
                and
                0<=x<W
                and
                0<=y<H
            ):

                temp[y][x]=p["kind"]

    return temp


# ==========================================================
# LOGO
# ==========================================================

def tetris_logo():

    return [
        "████████╗███████╗████████╗██████╗ ██╗███████╗",
        "╚══██╔══╝██╔════╝╚══██╔══╝██╔══██╗██║██╔════╝",
        "   ██║   █████╗     ██║   ██████╔╝██║███████╗",
        "   ██║   ██╔══╝     ██║   ██╔══██╗██║╚════██║",
        "   ██║   ███████╗   ██║   ██║  ██║██║███████║",
        "   ╚═╝   ╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝╚══════╝"
    ]


def preview_grid(p):

    return [
        [
            p["kind"]
            if (
                y<len(p["shape"])
                and
                x<len(p["shape"][y])
                and
                p["shape"][y][x]
            )
            else None
            for x in range(4)
        ]
        for y in range(4)
    ]


def draw_preview(p):

    out=[
        "┌────────┐"
    ]

    for row in preview_grid(p):

        out.append(
            "│"+
            "".join(
                "  "
                if v is None
                else cell(v)
                for v in row
            )+
            "│"
        )

    out.append(
        "└────────┘"
    )

    return out


def draw_empty_preview():

    return [
        "┌────────┐",
        "│        │",
        "│        │",
        "│   --   │",
        "│        │",
        "│        │",
        "└────────┘"
    ]
    # ==========================================================
# DIBUJAR PARTIDA
# ==========================================================

def draw_game(p,nxt):

    field=draw_field(
        make_board(p)
    )

    if hold:
        hb=draw_preview(
            newpiece(hold)
        )
    else:
        hb=draw_empty_preview()

    nb=draw_preview(nxt)

    side=[]

    side.append(
        " "+T("hold")
    )

    side+=hb

    side.append("")

    side.append(
        " "+T("next")
    )

    side+=nb

    out=[]

    title="TETRIS"

    if game_mode=="B":
        title+="  TYPE-B"

    out.append(
        "╔══════════════════════════════╗"
    )

    out.append(
        "║"+
        title.center(30)+
        "║"
    )

    out.append(
        "╠══════════════════════════════╣"
    )

    out.append(
        f"║ {T('score')}: {score:<8}"
        f"{T('lines')}: {lines:<6}║"
    )

    if game_mode=="B":

        out.append(
            f"║ {T('level')}: {level:<5}"
            f" OBJETIVO: {typeb_target:<8}║"
        )

    else:

        out.append(
            f"║ {T('level')}: "
            f"{level:<21}║"
        )

    out.append(
        "╠══════════════════════╦═══════╣"
    )

    for i,line in enumerate(field):

        extra=""

        if i<len(side):
            extra=side[i]

        out.append(
            line+
            " "+
            extra
        )

    out.append(
        "╚══════════════════════╩═══════╝"
    )

    out.append("")

    out.append(
        " A ←    S ↓    D →"
    )

    out.append(
        " SPACE = ROTAR    W = DROP"
    )

    out.append(
        " Q = HOLD         X = SALIR"
    )

    sys.stdout.write(
        "\033[H"+
        "\n".join(out)+
        "\033[J"
    )

    sys.stdout.flush()


# ==========================================================
# CONFIRMACIÓN DE SALIDA
# ==========================================================

def confirm_exit():

    while True:

        sys.stdout.write(
            "\033[2J\033[H"
        )

        print()

        print(
            "╔════════════════════════════╗"
        )

        print(
            "║     ¿SALIR DE LA PARTIDA? ║"
        )

        print(
            "╠════════════════════════════╣"
        )

        print(
            "║ ENTER = SÍ                 ║"
        )

        print(
            "║ X / ESC = NO               ║"
        )

        print(
            "╚════════════════════════════╝"
        )

        k=getkey()

        if k in ("\n","\r"):
            return True

        if k in ("x","esc"):
            return False

        time.sleep(.02)


# ==========================================================
# ANIMACIÓN DE LÍNEAS
# ==========================================================

def clear_animation(rows):

    if not rows:
        return

    temp=[
        r[:]
        for r in board
    ]

    order=[]

    for d in range(W):

        left=4-d
        right=5+d

        if 0<=left<W:
            order.append(left)

        if (
            0<=right<W
            and
            right!=left
        ):
            order.append(right)

    for x in order:

        for y in rows:
            temp[y][x]=None

        sys.stdout.write(
            "\033[H"+
            "\n".join(
                draw_field(temp)
            )+
            "\033[J"
        )

        sys.stdout.flush()

        time.sleep(.045)


def clear_lines():

    global score
    global lines
    global level

    rows=completed()

    if not rows:
        return 0

    clear_animation(rows)

    remaining=[
        board[y]
        for y in range(H)
        if y not in rows
    ]

    while len(remaining)<H:

        remaining.insert(
            0,
            [None]*W
        )

    board[:]=remaining

    n=len(rows)

    score+={
        1:100,
        2:200,
        3:300,
        4:500
    }.get(
        n,
        0
    )

    lines+=n

    # TYPE-A:
    # cada 10 líneas sube un nivel.

    if game_mode=="A":

        level=lines//10

    # TYPE-B:
    # el nivel permanece exactamente
    # en el seleccionado por el jugador.

    return n


# ==========================================================
# VELOCIDAD
# ==========================================================

def game_speed():

    base={
        "EASY":.70,
        "NORMAL":.55,
        "HARD":.40
    }[difficulty]

    return max(
        .05,
        base-level*.045
    )


# ==========================================================
# HOLD
# ==========================================================

def hold_piece(p,nxt):

    global hold
    global hold_used

    if hold_used:
        return p,nxt

    if hold is None:

        hold=p["kind"]

        p=nxt
        nxt=newpiece()

    else:

        old=hold

        hold=p["kind"]

        p=newpiece(old)

    hold_used=True

    return p,nxt


# ==========================================================
# LEADERBOARDS
# ==========================================================

def qualifies():

    return (
        len(data["scores"])<10
        or
        score>
        data["scores"][-1]["score"]
    )


def qualifies_typeb():

    return (
        len(data["typeb_scores"])<10
        or
        score>
        data["typeb_scores"][-1]["score"]
    )


def ask_name():

    sys.stdout.write(
        "\033[2J\033[H"
    )

    print()

    print(
        "╔════════════════════════════╗"
    )

    print(
        "║       NEW HIGH SCORE       ║"
    )

    print(
        "╠════════════════════════════╣"
    )

    print(
        f"║ {T('score')}: {score:<19}║"
    )

    print(
        f"║ {T('lines')}: {lines:<19}║"
    )

    print(
        f"║ {T('level')}: {level:<19}║"
    )

    print(
        "╠════════════════════════════╣"
    )

    print(
        f"║ {T('name')}: ",
        end=""
    )

    sys.stdout.flush()

    name=""

    while True:

        c=sys.stdin.read(1)

        if c in ("\n","\r"):
            break

        if c in (
            "\b",
            "\x7f"
        ):

            name=name[:-1]

            sys.stdout.write(
                "\r"+
                " "*25+
                "\r"+
                T("name")+
                ": "+
                name
            )

            sys.stdout.flush()

            continue

        if (
            c.isprintable()
            and
            len(name)<10
        ):

            name+=c

            sys.stdout.write(c)

            sys.stdout.flush()

    return (
        name.strip()
        or
        "PLAYER"
    )


def save_score():

    if not qualifies():
        return

    name=ask_name()

    data["scores"].append({
        "name":name[:10],
        "score":score,
        "lines":lines,
        "level":level
    })

    data["scores"].sort(
        key=lambda x:x["score"],
        reverse=True
    )

    # CORREGIDO:
    data["scores"]=data["scores"][:10]

    save_data()


def save_typeb_score():

    if not qualifies_typeb():
        return

    name=ask_name()

    data["typeb_scores"].append({
        "name":name[:10],
        "score":score,
        "lines":lines,
        "level":level,
        "height":typeb_height
    })

    data["typeb_scores"].sort(
        key=lambda x:x["score"],
        reverse=True
    )

    # CORREGIDO:
    data["typeb_scores"]=data["typeb_scores"][:10]


    save_data()


# ==========================================================
# CINEMÁTICAS TYPE-B
# ==========================================================

def typeb_cinematic():

    # La cinematica cambia dependiendo
    # del nivel y handicap seleccionados.

    difficulty_value={
        "EASY":0,
        "NORMAL":1,
        "HARD":2
    }[difficulty]

    intensity=(
        level+
        typeb_height+
        difficulty_value
    )

    frames=[]

    if intensity<5:

        frames=[
            [
                "╔══════════════════════════════╗",
                "║                              ║",
                "║          TYPE-B              ║",
                "║                              ║",
                "║       25 LÍNEAS              ║",
                "║                              ║",
                "║          ★                   ║",
                "╚══════════════════════════════╝"
            ],

            [
                "╔══════════════════════════════╗",
                "║                              ║",
                "║          TYPE-B              ║",
                "║                              ║",
                "║       25 LÍNEAS              ║",
                "║                              ║",
                "║        ★ ★                   ║",
                "╚══════════════════════════════╝"
            ],

            [
                "╔══════════════════════════════╗",
                "║                              ║",
                "║        ¡COMPLETADO!          ║",
                "║                              ║",
                "║       TYPE-B CLEAR           ║",
                "║                              ║",
                "║       ★ ★ ★                  ║",
                "╚══════════════════════════════╝"
            ]
        ]

    elif intensity<10:

        frames=[
            [
                "╔══════════════════════════════╗",
                "║                              ║",
                "║       CONGRATULATIONS!       ║",
                "║                              ║",
                "║          TYPE-B              ║",
                "║                              ║",
                "║        ★    ★                ║",
                "╚══════════════════════════════╝"
            ],

            [
                "╔══════════════════════════════╗",
                "║                              ║",
                "║       CONGRATULATIONS!       ║",
                "║                              ║",
                "║        25 LINES CLEAR        ║",
                "║                              ║",
                "║      ★    ★    ★             ║",
                "╚══════════════════════════════╝"
            ],

            [
                "╔══════════════════════════════╗",
                "║                              ║",
                "║          TYPE-B              ║",
                "║                              ║",
                "║        CLEAR COMPLETE        ║",
                "║                              ║",
                "║    ★ ★ ★ ★ ★ ★ ★             ║",
                "╚══════════════════════════════╝"
            ]
        ]

    else:

        frames=[
            [
                "╔══════════════════════════════╗",
                "║                              ║",
                "║      CONGRATULATIONS!        ║",
                "║                              ║",
                "║          LEVEL 9             ║",
                "║                              ║",
                "║      ★ ★ ★ ★ ★ ★ ★ ★         ║",
                "╚══════════════════════════════╝"
            ],

            [
                "╔══════════════════════════════╗",
                "║                              ║",
                "║       TYPE-B COMPLETE        ║",
                "║                              ║",
                "║       HIGH HANDICAP          ║",
                "║                              ║",
                "║   ★ ★ ★ ★ ★ ★ ★ ★ ★ ★       ║",
                "╚══════════════════════════════╝"
            ],

            [
                "╔══════════════════════════════╗",
                "║                              ║",
                "║        MASTER CLEAR          ║",
                "║                              ║",
                "║       LEVEL 9 / MAX          ║",
                "║                              ║",
                "║       ★ ★ ★ ★ ★              ║",
                "╚══════════════════════════════╝"
            ]
        ]

    for frame in frames:

        sys.stdout.write(
            "\033[2J\033[H"+
            "\n".join(frame)
        )

        sys.stdout.flush()

        time.sleep(.55)

    time.sleep(.7)
    # ==========================================================
# GAME OVER
# ==========================================================

def game_over():

    # Type-B solamente puede registrar
    # una partida completada.

    if game_mode=="B":

        if lines>=typeb_target:

            save_typeb_score()

    else:

        save_score()

    while True:

        sys.stdout.write(
            "\033[2J\033[H"
        )

        print()

        print(
            "╔════════════════════════════╗"
        )

        print(
            "║         GAME OVER          ║"
        )

        print(
            "╠════════════════════════════╣"
        )

        print(
            f"║ {T('score')}: {score:<19}║"
        )

        print(
            f"║ {T('lines')}: {lines:<19}║"
        )

        print(
            f"║ {T('level')}: {level:<19}║"
        )

        print(
            "╠════════════════════════════╣"
        )

        print(
            "║ ENTER = MENÚ               ║"
        )

        print(
            "║ X = SALIR                  ║"
        )

        print(
            "╚════════════════════════════╝"
        )

        k=getkey()

        if k in ("\n","\r"):
            return

        if k=="x":
            return "quit"

        time.sleep(.02)


# ==========================================================
# PARTIDA
# ==========================================================

def play_game(
    handicap,
    diff,
    startlevel,
    mode="A"
):

    global board
    global score
    global lines
    global level
    global hold
    global hold_used
    global difficulty
    global game_mode
    global typeb_height

    game_mode=mode

    board=[
        [None]*W
        for _ in range(H)
    ]

    score=0
    lines=0
    level=startlevel

    hold=None
    hold_used=False

    difficulty=diff
    typeb_height=handicap

    # Handicap Type-B.
    # Las filas aparecen en la parte inferior
    # dejando un hueco aleatorio.

    for y in range(
        H-handicap,
        H
    ):

        hole=random.randrange(W)

        for x in range(W):

            if x!=hole:

                board[y][x]=random.choice(
                    list(PIECES)
                )

    p=newpiece()
    nxt=newpiece()

    if collide(p):

        return game_over()

    last=time.monotonic()

    while True:

        k=getkey()

        if k=="x":

            if confirm_exit():

                return

            last=time.monotonic()

            continue

        elif k in (
            "a",
            "left"
        ):

            move(
                p,
                -1,
                0
            )

        elif k in (
            "d",
            "right"
        ):

            move(
                p,
                1,
                0
            )

        elif k in (
            "s",
            "down"
        ):

            if not move(
                p,
                0,
                1
            ):

                lock_piece(p)

                clear_lines()

                # Type-B termina inmediatamente
                # al alcanzar 25 líneas.

                if (
                    game_mode=="B"
                    and
                    lines>=typeb_target
                ):

                    typeb_cinematic()

                    if qualifies_typeb():

                        save_typeb_score()

                    return "typeb_complete"

                p=nxt
                nxt=newpiece()

                hold_used=False

                if collide(p):

                    return game_over()

            last=time.monotonic()

        elif k==" ":

            rotate_piece(p)

        elif k=="w":

            hard_drop(p)

            lock_piece(p)

            clear_lines()

            if (
                game_mode=="B"
                and
                lines>=typeb_target
            ):

                typeb_cinematic()

                if qualifies_typeb():

                    save_typeb_score()

                return "typeb_complete"

            p=nxt
            nxt=newpiece()

            hold_used=False

            if collide(p):

                return game_over()

            last=time.monotonic()

        elif k=="q":

            p,nxt=hold_piece(
                p,
                nxt
            )

            if collide(p):

                return game_over()

            last=time.monotonic()

        now=time.monotonic()

        if now-last>=game_speed():

            if not move(
                p,
                0,
                1
            ):

                lock_piece(p)

                clear_lines()

                if (
                    game_mode=="B"
                    and
                    lines>=typeb_target
                ):

                    typeb_cinematic()

                    if qualifies_typeb():

                        save_typeb_score()

                    return "typeb_complete"

                p=nxt
                nxt=newpiece()

                hold_used=False

                if collide(p):

                    return game_over()

            last=now

        draw_game(
            p,
            nxt
        )

        time.sleep(.008)


# ==========================================================
# CONFIGURACIÓN DE PARTIDA
# ==========================================================

def game_setup():

    mode=0

    values=[
        0,      # handicap
        0,      # nivel
        1       # dificultad NORMAL
    ]

    selected=0

    while True:

        diffs=[
            T("easy"),
            T("normal"),
            T("hard")
        ]

        modes=[
            "TYPE-A",
            "TYPE-B"
        ]

        sys.stdout.write(
            "\033[2J\033[H"
        )

        print()

        print(
            "╔══════════════════════════════╗"
        )

        print(
            "║      CONFIGURAR PARTIDA      ║"
        )

        print(
            "╠══════════════════════════════╣"
        )

        opts=[
            f"MODO: {modes[mode]}",
            f"HANDICAP: {values[0]}",
            f"NIVEL: {values[1]}",
            f"DIFICULTAD: {diffs[values[2]]}"
        ]

        for i,o in enumerate(opts):

            mark=(
                "> "
                if i==selected
                else "  "
            )

            print(
                "║ "+
                mark+
                o.ljust(26)+
                " ║"
            )

        print(
            "╠══════════════════════════════╣"
        )

        print(
            "║ W/S = OPCIÓN                 ║"
        )

        print(
            "║ A/D = CAMBIAR                ║"
        )

        print(
            "║ ENTER = JUGAR                ║"
        )

        print(
            "║ X = VOLVER                   ║"
        )

        print(
            "╚══════════════════════════════╝"
        )

        k=getkey()

        if k in (
            "w",
            "up"
        ):

            selected=(
                selected-1
            )%4

        elif k in (
            "s",
            "down"
        ):

            selected=(
                selected+1
            )%4

        elif k in (
            "a",
            "left"
        ):

            if selected==0:

                mode=(
                    mode-1
                )%2

            elif selected==1:

                values[0]=max(
                    0,
                    values[0]-1
                )

            elif selected==2:

                values[1]=max(
                    0,
                    values[1]-1
                )

            else:

                values[2]=(
                    values[2]-1
                )%3

        elif k in (
            "d",
            "right"
        ):

            if selected==0:

                mode=(
                    mode+1
                )%2

            elif selected==1:

                values[0]=min(
                    5,
                    values[0]+1
                )

            elif selected==2:

                values[1]=min(
                    9,
                    values[1]+1
                )

            else:

                values[2]=(
                    values[2]+1
                )%3

        elif k in (
            "\n",
            "\r"
        ):

            result=play_game(
                values[0],
                [
                    "EASY",
                    "NORMAL",
                    "HARD"
                ][values[2]],
                values[1],
                "B"
                if mode==1
                else "A"
            )

            if result=="typeb_complete":

                # El siguiente nivel NO se inicia
                # automáticamente.
                # El jugador vuelve a seleccionar
                # nivel/handicap.

                continue

            if result=="quit":

                return "quit"

        elif k=="x":

            return

        time.sleep(.02)


# ==========================================================
# LEADERBOARD
# ==========================================================

def show_scores(
    scores,
    title
):

    while True:

        sys.stdout.write(
            "\033[2J\033[H"
        )

        print()

        print(
            "╔══════════════════════════════╗"
        )

        print(
            "║ "+
            title.center(28)+
            "║"
        )

        print(
            "╠══════════════════════════════╣"
        )

        for i,s in enumerate(scores):

            print(
                f"║ {i+1:2}. "
                f"{s['name'][:10]:10} "
                f"{s['score']:7} "
                f"L{s['lines']:3} "
                f"Lv{s['level']:2} ║"
            )

        print(
            "╚══════════════════════════════╝"
        )

        print()

        print(
            "ENTER / X = "+T("back")
        )

        k=getkey()

        if k in (
            "\n",
            "\r",
            "x"
        ):

            return

        time.sleep(.02)


def scores_menu():

    selected=0

    while True:

        opts=[
            T("scores"),
            T("typeb_scores")
        ]

        sys.stdout.write(
            "\033[2J\033[H"
        )

        print()

        print(
            "╔══════════════════════════════╗"
        )

        print(
            "║       LEADERBOARDS           ║"
        )

        print(
            "╠══════════════════════════════╣"
        )

        for i,o in enumerate(opts):

            mark=(
                "> "
                if i==selected
                else "  "
            )

            print(
                "║ "+
                mark+
                o.ljust(26)+
                " ║"
            )

        print(
            "╠══════════════════════════════╣"
        )

        print(
            "║ W/S = SELECCIONAR            ║"
        )

        print(
            "║ ENTER = ACEPTAR              ║"
        )

        print(
            "║ X = VOLVER                   ║"
        )

        print(
            "╚══════════════════════════════╝"
        )

        k=getkey()

        if k in (
            "w",
            "up"
        ):

            selected=(
                selected-1
            )%2

        elif k in (
            "s",
            "down"
        ):

            selected=(
                selected+1
            )%2

        elif k in (
            "\n",
            "\r"
        ):

            if selected==0:

                show_scores(
                    data["scores"],
                    T("scores")
                )

            else:

                show_scores(
                    data["typeb_scores"],
                    T("typeb_scores")
                )

        elif k=="x":

            return

        time.sleep(.02)
        # ==========================================================
# CONFIGURACIÓN GENERAL
# ==========================================================

def config_menu():

    selected=0

    styles=[
        "NES",
        "ATARI ARCADE",
        "PC DOS",
        "ASCII",
        "SIMPLE"
    ]

    ascii_palettes=[
        "MONO",
        "CYAN",
        "GREEN",
        "WHITE",
        "YELLOW"
    ]

    while True:

        if config["style"]=="ASCII":

            opts=[
                f"ESTILO: {config['style']}",
                f"PALETA ASCII: {config['ascii_palette']}",
                f"GRID: {'ON' if config.get('grid',True) else 'OFF'}",
                f"IDIOMA: {config.get('language','ES')}"
            ]

        else:

            opts=[
                f"ESTILO: {config['style']}",
                "PALETA: INTEGRADA",
                f"GRID: {'ON' if config.get('grid',True) else 'OFF'}",
                f"IDIOMA: {config.get('language','ES')}"
            ]

        sys.stdout.write(
            "\033[2J\033[H"
        )

        print()

        print(
            "╔══════════════════════════════╗"
        )

        print(
            "║         CONFIGURACIÓN        ║"
        )

        print(
            "╠══════════════════════════════╣"
        )

        for i,o in enumerate(opts):

            mark=(
                "> "
                if i==selected
                else "  "
            )

            print(
                "║ "+
                mark+
                o.ljust(26)+
                " ║"
            )

        print(
            "╠══════════════════════════════╣"
        )

        print(
            "║ W/S = OPCIÓN                 ║"
        )

        print(
            "║ A/D = CAMBIAR                ║"
        )

        print(
            "║ X = VOLVER                   ║"
        )

        print(
            "╚══════════════════════════════╝"
        )

        k=getkey()

        if k in (
            "w",
            "up"
        ):

            selected=(
                selected-1
            )%4

        elif k in (
            "s",
            "down"
        ):

            selected=(
                selected+1
            )%4

        elif k in (
            "a",
            "left",
            "d",
            "right"
        ):

            direction=(
                -1
                if k in (
                    "a",
                    "left"
                )
                else 1
            )

            if selected==0:

                i=styles.index(
                    config["style"]
                )

                config["style"]=styles[
                    (i+direction)
                    %len(styles)
                ]

            elif selected==1:

                if config["style"]=="ASCII":

                    i=ascii_palettes.index(
                        config["ascii_palette"]
                    )

                    config["ascii_palette"]=ascii_palettes[
                        (i+direction)
                        %len(ascii_palettes)
                    ]

            elif selected==2:

                config["grid"]=not config.get(
                    "grid",
                    True
                )

            elif selected==3:

                config["language"]=(
                    "EN"
                    if config.get(
                        "language",
                        "ES"
                    )=="ES"
                    else "ES"
                )

            save_data()

        elif k=="x":

            save_data()

            return

        time.sleep(.02)


# ==========================================================
# INSTRUCCIONES
# ==========================================================

def instructions():

    while True:

        sys.stdout.write(
            "\033[2J\033[H"
        )

        print()

        print(
            "╔══════════════════════════════╗"
        )

        print(
            "║        INSTRUCCIONES         ║"
        )

        print(
            "╠══════════════════════════════╣"
        )

        print(
            "║ A       ← IZQUIERDA          ║"
        )

        print(
            "║ S       ↓ ABAJO              ║"
        )

        print(
            "║ D       → DERECHA            ║"
        )

        print(
            "║ SPACE   ROTAR                ║"
        )

        print(
            "║ W       HARD DROP             ║"
        )

        print(
            "║ Q       HOLD                 ║"
        )

        print(
            "║ X       SALIR                ║"
        )

        print(
            "╠══════════════════════════════╣"
        )

        print(
            "║ TYPE-A:                      ║"
        )

        print(
            "║ 1 LÍNEA  = 100               ║"
        )

        print(
            "║ 2 LÍNEAS = 200               ║"
        )

        print(
            "║ 3 LÍNEAS = 300               ║"
        )

        print(
            "║ TETRIS   = 500               ║"
        )

        print(
            "║ CADA 10 LÍNEAS = +1 NIVEL    ║"
        )

        print(
            "╠══════════════════════════════╣"
        )

        print(
            "║ TYPE-B:                      ║"
        )

        print(
            "║ 25 LÍNEAS PARA COMPLETAR     ║"
        )

        print(
            "║ NIVEL + HANDICAP SELECCION.  ║"
        )

        print(
            "║ NO SUBE AUTOMÁTICAMENTE       ║"
        )

        print(
            "║ AL COMPLETAR: CINEMÁTICA     ║"
        )

        print(
            "╚══════════════════════════════╝"
        )

        print()

        print(
            "ENTER / X = VOLVER"
        )

        k=getkey()

        if k in (
            "\n",
            "\r",
            "x"
        ):

            return

        time.sleep(.02)


# ==========================================================
# SALIDA SEGURA
# ==========================================================

def emergency_exit(
    signum=None,
    frame=None
):

    try:

        save_data()

    except:

        pass

    try:

        sys.stdout.write(
            "\033[?25h"
            "\033[2J\033[H"
        )

        sys.stdout.flush()

    except:

        pass

    raise SystemExit


# ==========================================================
# MENÚ PRINCIPAL
# ==========================================================

def start_menu():

    selected=0

    opts_keys=[
        "play",
        "scores",
        "config",
        "instructions",
        "quit"
    ]

    while True:

        opts=[
            T(k)
            for k in opts_keys
        ]

        sys.stdout.write(
            "\033[2J\033[H"
        )

        logo=tetris_logo()

        # Frase arriba del logo,
        # como en la presentación clásica.

        print(
            "The relentless building block".center(32)
        )

        print(
            "video puzzle.".center(32)
        )

        print()

        for line in logo:

            print(
                line.center(32)
            )

        # El texto que antes decía
        # TERMINAL EDITION queda debajo
        # del logo.

        print()

        print(
            "TERMINAL EDITION".center(32)
        )

        print()

        print(
            "╔══════════════════════════════╗"
        )

        for i,o in enumerate(opts):

            mark=(
                "> "
                if i==selected
                else "  "
            )

            print(
                "║ "+
                mark+
                o.ljust(26)+
                " ║"
            )

        print(
            "╠══════════════════════════════╣"
        )

        print(
            "║ W/S = SELECCIONAR            ║"
        )

        print(
            "║ ENTER = ACEPTAR              ║"
        )

        print(
            "╚══════════════════════════════╝"
        )

        sys.stdout.flush()

        k=getkey()

        if k in (
            "w",
            "up"
        ):

            selected=(
                selected-1
            )%5

        elif k in (
            "s",
            "down"
        ):

            selected=(
                selected+1
            )%5

        elif k in (
            "\n",
            "\r"
        ):

            if selected==0:

                result=game_setup()

                if result=="quit":

                    return "quit"

            elif selected==1:

                scores_menu()

            elif selected==2:

                config_menu()

            elif selected==3:

                instructions()

            elif selected==4:

                return "quit"

        time.sleep(.02)


# ==========================================================
# MAIN
# ==========================================================

def main():

    old=termios.tcgetattr(
        sys.stdin.fileno()
    )

    tty.setcbreak(
        sys.stdin.fileno()
    )

    signal.signal(
        signal.SIGINT,
        emergency_exit
    )

    if hasattr(
        signal,
        "SIGTERM"
    ):

        signal.signal(
            signal.SIGTERM,
            emergency_exit
        )

    if hasattr(
        signal,
        "SIGHUP"
    ):

        signal.signal(
            signal.SIGHUP,
            emergency_exit
        )

    try:

        sys.stdout.write(
            "\033[?25l"
            "\033[2J\033[H"
        )

        sys.stdout.flush()

        start_menu()

    finally:

        termios.tcsetattr(
            sys.stdin,
            termios.TCSADRAIN,
            old
        )

        sys.stdout.write(
            "\033[?25h"
        )

        sys.stdout.write(
            "\033[2J\033[H"
        )

        sys.stdout.flush()


if __name__=="__main__":

    main()