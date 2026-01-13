import keyboard_keys as keys

EV_KEY_A = 30
EV_KEY_B = 48
EV_KEY_C = 46
EV_KEY_D = 32
EV_KEY_E = 18
EV_KEY_F = 33
EV_KEY_G = 34
EV_KEY_H = 35
EV_KEY_I = 23
EV_KEY_J = 36
EV_KEY_K = 37
EV_KEY_L = 38
EV_KEY_M = 50
EV_KEY_N = 49
EV_KEY_O = 24
EV_KEY_P = 25
EV_KEY_Q = 16
EV_KEY_R = 19
EV_KEY_S = 31
EV_KEY_T = 20
EV_KEY_U = 22
EV_KEY_V = 47
EV_KEY_W = 17
EV_KEY_X = 45
EV_KEY_Y = 21
EV_KEY_Z = 44


MOD_RIGHT_ALT = 100
MOD_RIGHT_SHIFT = 54
MOD_RIGHT_CTRL = 97
MOD_LEFT_SHIFT = 42
MOD_LEFT_CTRL = 29
MOD_LEFT_ALT = 56

EV_MODIFIERS = {
    MOD_LEFT_SHIFT: keys.LEFT_SHIFT,
    MOD_RIGHT_SHIFT: keys.RIGHT_SHIFT,
    MOD_LEFT_CTRL: keys.LEFT_CTRL,
    MOD_RIGHT_CTRL: keys.RIGHT_CTRL,
    MOD_LEFT_ALT: keys.LEFT_ALT,
    MOD_RIGHT_ALT: keys.RIGHT_ALT,
}

EV_TO_HID = {
    EV_KEY_A: keys.KEY_A,
    EV_KEY_B: keys.KEY_B,
    EV_KEY_C: keys.KEY_C,
    EV_KEY_D: keys.KEY_D,
    EV_KEY_E: keys.KEY_E,
    EV_KEY_F: keys.KEY_F,
    EV_KEY_G: keys.KEY_G,
    EV_KEY_H: keys.KEY_H,
    EV_KEY_I: keys.KEY_I,
    EV_KEY_J: keys.KEY_J,
    EV_KEY_K: keys.KEY_K,
    EV_KEY_L: keys.KEY_L,
    EV_KEY_M: keys.KEY_M,
    EV_KEY_N: keys.KEY_N,
    EV_KEY_O: keys.KEY_O,
    EV_KEY_P: keys.KEY_P,
    EV_KEY_Q: keys.KEY_Q,
    EV_KEY_R: keys.KEY_R,
    EV_KEY_S: keys.KEY_S,
    EV_KEY_T: keys.KEY_T,
    EV_KEY_U: keys.KEY_U,
    EV_KEY_V: keys.KEY_V,
    EV_KEY_W: keys.KEY_W,
    EV_KEY_X: keys.KEY_X,
    EV_KEY_Y: keys.KEY_Y,
    EV_KEY_Z: keys.KEY_Z,
}