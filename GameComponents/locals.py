SCREEN_DIMENSION = (800, 800)
BG_COLOR = (15, 15, 25)
WINDOW_TITLE = "Asteroid game"
TESTSQUARE = 'testsquare'

PLAYER = 'player'
INV_PLAYER = 'invPlayer'
MAX_SPEED = 150           # px per sec
ACC = 300     # 150          # px per sec^2
MAX_TURN_SPEED = 220      # degrees per sec
TURN_ACC = 3000    #270   # degrees per sec^2
TURN_MULTIPLIER_PF = 0    # 0.98  
BREAK_MULTIPLIER = 0.015       # 0.01
INVINCIBLE_TIME = 5       # in sec

BULLET = 'bullet'
BULLET_SPEED = 20

ASTEROID_SPD = 80
ASTEROID_ANIM_TORQUE = 25
ASTS = ['ast1', 'ast2', 'ast3', 'ast4', 'ast5', 'ast6']
AST_FREQUECY = 5          # an asteroid every {AST_FREQUECY} sec
SMALL_ASTS_PDA = (1, 3)
POINTS_P_AST = 100        # for big, smalls are half that

UPD = 60

TYPEWRITER_FONT = "typewriter.ttf"
DEFAULT_TEXT_COL = (235, 235, 235)

TITLE_TXT = "Asteroid game"
TITLE_SIZE = 40
SELECTABLE_SIZE = 27
SCORE_SIZE = 20
HEART = "heart"

ARROW = "arrow"

PARTICLE_PARENT_LIFETIME = 2 # sec
PARTICLE_LIFETIME = 0.65
PARTICLE_SPD = 100 # px/sec
PARTICLE_MIN = 10
PARTICLE_MAX = 16

DEFAULT_PORT = 6385

LINE = "line"

COM_GAMEDATINFO = "cgamedinfo"
COM_PREP = "cprep"

COM_REQUEST_JOIN = "creqjoin"
COM_GAME_FULL = "cgfull"
COM_CON_SUCCESS = "csuccess"
COM_ASTEROID = "cast"
COM_SMALL_AST = "csast"
COM_BULLET = "cbullet"
COM_PLAYER_POS = "cplayerpos"
COM_GAME_START = "cstart"
COM_PING = "cping"
COM_SHOOT = "cshoot"
COM_DEST_BULLET = "cdbullet"
COM_DEST_AST = "cdast"

NAMETAG_OFFSET = (0, 15)

TIMEOUT = 10
TIMEOUT_CHECK_RATE = 2  # seconds

DELIMITER = "/x/"


