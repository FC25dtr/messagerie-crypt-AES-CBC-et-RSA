import copy

#CONFIGURATIONS
polynome = 0b100011011 
c = 0b01100011 
matrix_mix_columns = [[2,3,1,1],[1,2,3,1],[1,1,2,3],[3,1,1,2]]
matrix_invmix_columns = [[0xe,0xb,0xd,0x9],[0x9,0xe,0xb,0xd],[0xd,0x9,0xe,0xb],[0xb,0xd,0x9,0xe]]

#FONCTIONS UTILITAIRES

def tohex(n):
    if n < 16: return '0'+hex(n)[-1] 
    else: return hex(n)[2:]

def affiche(L):
    print(list(map(tohex,L[0])))
    print(list(map(tohex,L[1])))
    print(list(map(tohex,L[2])))
    print(list(map(tohex,L[3])))
    print()

def convert_to_state(message):
    state = [0]*4
    for i in range(4):
        state[i] = [ord(message[0:4][i]),ord(message[4:8][i]),ord(message[8:12][i]),ord(message[12:16][i])]
    return state

def multbyalpha(x):
    y = x << 1
    if (y & (1 << 8)):
        y = y ^ polynome
    return y

def multbygen(x):
    return (multbyalpha(x)^x)

def construit_F_2_8():
    table = [1]
    log_t = [0]*256
    log_t[0] = -1
    log_t[1] = 0
    for i in range(1,255):
        aux = multbygen(table[i-1])
        table = table + [aux]
        log_t[aux] = i
    table += [1]
    return table, log_t

gen, log_gen = construit_F_2_8()

def mult(a,b):
    if (a == 0) or (b == 0): return 0
    idxa = log_gen[a]
    idxb = log_gen[b]
    return gen[(idxa+idxb) % 255]

def multiplication(a, b):
    if a == 0 or b == 0: return 0
    return gen[(log_gen[a] + log_gen[b]) % 255]

def inv(x):
    if x == 0: return 0
    idx = log_gen[x]
    return gen[255-idx]

#TRANSFORMATIONS AES

def matvecbin(M,R):
    L = 0
    tmp = R
    res = 0 
    for i in range(len(M)):
        for k in range(len(M[i])):
            res = res ^ M[i][k]&(R&1)
            R = R >> 1
        R = tmp 
        L = L | (res << i)
        res = 0
    return L

def XORliste(b,e):
    res = 0
    for i in range(len(b)):
        res = res ^ (((e&1) ^b [i])<<i)
        e = e >>1
    return res 

def Subbytes(etat):
    A = [[1,0,0,0,1,1,1,1],[1,1,0,0,0,1,1,1],[1,1,1,0,0,0,1,1],
         [1,1,1,1,0,0,0,1],[1,1,1,1,1,0,0,0],[0,1,1,1,1,1,0,0],
         [0,0,1,1,1,1,1,0],[0,0,0,1,1,1,1,1]]
    b = [1,1,0,0,0,1,1,0]
    resultat = [ligne[:] for ligne in etat] 
    for i in range(len(resultat)):
        for j in range(len(resultat[i])):
            tmp = inv(resultat[i][j])
            tmp1 = matvecbin(A, tmp)
            resultat[i][j] = XORliste(b, tmp1)
    return resultat

def ShiftRows(etat):
    tmp = etat[0]
    tmp1 = etat[1]
    tmp2 = etat[2]
    tmp3 = etat[3]  
    return [tmp, tmp1[1:]+[tmp1[0]], tmp2[2:]+tmp2[:2], tmp3[3:]+tmp3[:3]]

def MixColumns(etat):
    matrice = [[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]]
    for k in range(len(etat)):
        for i in range(len(etat)):
            tmp = 0
            for j in range(len(etat)):
                tmp1 = multiplication(matrix_mix_columns[k][j], etat[j][i])
                tmp = tmp ^ tmp1
            matrice[k][i] = tmp
    return matrice

def AddRoundKey(etat, tour):
    state = []
    K = [0,0,0,0]
    for i in range(4):
        K[i] = W[i][4*tour:4*(tour+1)]
    for i in range(4):
        aux = []
        for j in range(4):
            aux = aux + [etat[i][j] ^ K[i][j]]
        state = state + [aux]
    return state

# GESTION CLÉ 
def S(x):
    if x == 0:
        y = 0
    else:
        y = inv(x)
    result = 0
    for i in range(8):
        result = result ^ ((((y >> i) & 1)^((y >>((i+4) % 8)) & 1)^((y >> ((i+5) % 8)) & 1)^((y >> ((i+6) % 8)) & 1)^((y >> ((i+7) % 8)) & 1)^((c >> i) & 1)) << i)
    return result

def gen_cles(k):
    global W    
    RC = [0,1]
    for i in range(2,11):
        RC = RC + [multbyalpha(RC[i-1])]
    W_ = [[0]*4 for _ in range(44)]
    cle_convert = convert_to_state(k)
    for j in range(4):
        for i in range(4):
            W_[i][j] = cle_convert[j][i]
    for i in range(4,44):
        temp = W_[i-1]
        if (i % 4) == 0 :
            temp = list(map(S,temp[1:]+[temp[0]]))
            temp[0] ^= RC[i//4]
        for j in range(4):
            W_[i][j] = W_[i-4][j] ^ temp[j]
    return transforme(W_)

def transforme(W):
    L=[0]*4
    for i in range(4):
        L[i] = [0]*44
        for j in range(44):
            L[i][j] = W[j][i]
    return L

#CREATION SBOX

SBOX = [S(i) for i in range(256)]
INVsbox = [0] * 256
for i in range(256):
    INVsbox[SBOX[i]] = i

#FONCTIONS INVERSES

def INVSubbytes(etat):
    liste = []
    for i in range(4):
        l = []
        for j in range(4):
            l += [INVsbox[etat[i][j]]]
        liste += [l]
    return liste

def INVShiftRows(etat):
    state = [etat[0]]
    state = state + [[etat[1][3]] + etat[1][:3]]
    state = state + [etat[2][2:] + etat[2][0:2]]
    state = state + [etat[3][1:] + [etat[3][0]]]
    return state

def INVMixColumns(etat):
    state = []
    for i in range(4):
        aux = []
        for j in range(4):
            somme = 0
            for k in range(4):
                somme = somme ^ mult(matrix_invmix_columns[i][k], etat[k][j])
            aux = aux + [somme]
        state = state + [aux]
    return state 

def INVAddRoundKey(etat, tour):
    state = []
    K = [0,0,0,0]
    for i in range(4):
        K[i] = W[i][4*tour:4*(tour+1)]
    K = INVMixColumns(K)
    for i in range(4):
        aux = []
        for j in range(4):
            aux = aux + [etat[i][j] ^ K[i][j]]
        state = state + [aux]
    return state

def string_to_bytes(etat):
    while len(etat) % 16 != 0:
        etat += '\x00'
    tab = []
    saut, saut1 = 0, 16
    while len(etat) > saut1:
        tab += [convert_to_state(etat[saut:saut1])]
        saut += 16
        saut1 += 16
    tab += [convert_to_state(etat[saut:])] 
    return tab

def bytes_to_string(tab):
    res = ""
    for i in range(len(tab)):
        for k in range(4):
            for j in range(4):
                res += chr(tab[i][j][k])
    return res.rstrip('\x00')

def CBC_chiffrement_aes(message,IV):
    tab = string_to_bytes(message)
    for i in range(len(tab)):
        for j in range(4):
            for k in range(4):
                tab[i][j][k] = tab[i][j][k] ^ IV[j][k]
        tab[i] = AddRoundKey(tab[i], 0)
        for l in range(1,10):
            tab[i] = Subbytes(tab[i])
            tab[i] = ShiftRows(tab[i])
            tab[i] = MixColumns(tab[i])
            tab[i] = AddRoundKey(tab[i], l)
        tab[i] = Subbytes(tab[i])
        tab[i] = ShiftRows(tab[i])
        tab[i] = AddRoundKey(tab[i], 10)
        IV = tab[i]
    return tab

def CBC_dechiffrement_aes(tab, IV):
    tab_bis = copy.deepcopy(tab)
    for i in range(len(tab)):
        tab[i] = AddRoundKey(tab[i], 10)
        for l in range(9, 0, -1):
            tab[i] = INVSubbytes(tab[i])
            tab[i] = INVShiftRows(tab[i])
            tab[i] = INVMixColumns(tab[i])
            tab[i] = INVAddRoundKey(tab[i], l)
        tab[i] = INVSubbytes(tab[i])
        tab[i] = INVShiftRows(tab[i])
        tab[i] = AddRoundKey(tab[i], 0)
        prev = IV if i == 0 else tab_bis[i-1]
        for j in range(4):
            for k in range(4):
                tab[i][j][k] = tab[i][j][k] ^ prev[j][k]
    res = bytes_to_string(tab)
    return res
    
cle1 = "Ceci est une cle"
W = gen_cles(cle1)

# TEST CBC (Message long)
IV = [[0x12,0x90,0x12,0x90],[0x34,0xab,0x34,0xab],[0x56,0xcd,0x56,0xcd],[0x78,0xef,0x78,0xef]]
etat2 = "J'adore vraiment la cryptographie,bien plus que le developpement"
tab = string_to_bytes(etat2)

print("--- CHIFFREMENT CBC ---")
for i in range(len(tab)):
    for j in range(4):
        for k in range(4):
            tab[i][j][k] = tab[i][j][k] ^ IV[j][k]
    tab[i] = AddRoundKey(tab[i], 0)
    for l in range(1,10):
        tab[i] = Subbytes(tab[i])
        tab[i] = ShiftRows(tab[i])
        tab[i] = MixColumns(tab[i])
        tab[i] = AddRoundKey(tab[i], l)
    tab[i] = Subbytes(tab[i])
    tab[i] = ShiftRows(tab[i])
    tab[i] = AddRoundKey(tab[i], 10)
    IV = tab[i]
    affiche(tab[i])

# TEST DECHIFFREMENT (etat3)
print("--- DECHIFFREMENT ETAT3 ---")
etat3=[
  [[0xfb,0x6c,0x44,0x9b],[0x9f,0xe3,0xa4,0x2a],[0xa6,0x5b,0x4c,0x88],[0xe6,0xd8,0x14,0x8f]],
  [[0xdc,0x07,0x18,0x67],[0x05,0x21,0x35,0x7c],[0x01,0x06,0xe3,0x15],[0xc7,0x69,0x8b,0x9b]],
  [[0x76,0x1d,0x6a,0x4b],[0x66,0xd4,0x6c,0x23],[0xde,0x0b,0x66,0xc6],[0x20,0x95,0x89,0x44]],
  [[0xaf,0x2c,0x39,0xc6],[0xd3,0xe6,0xed,0xb5],[0x84,0x48,0x85,0xb8],[0x1c,0x2f,0xf6,0x9c]]
]
IV2 = [[0x12,0x90,0x12,0x90],[0x34,0xab,0x34,0xab],[0x56,0xcd,0x56,0xcd],[0x78,0xef,0x78,0xef]]
etat3bis = copy.deepcopy(etat3)

for i in range(len(etat3)):
    etat3[i] = AddRoundKey(etat3[i],10)
    for l in range(9,0,-1):
        etat3[i] = INVSubbytes(etat3[i])
        etat3[i] = INVShiftRows(etat3[i])
        etat3[i] = INVMixColumns(etat3[i])
        etat3[i] = INVAddRoundKey(etat3[i],l)
    etat3[i] = INVSubbytes(etat3[i])
    etat3[i] = INVShiftRows(etat3[i])
    etat3[i] = AddRoundKey(etat3[i],0)
    prev = IV2 if i == 0 else etat3bis[i-1]
    for j in range(4):
        for k in range(4):
            etat3[i][j][k] = etat3[i][j][k] ^ prev[j][k]

res = bytes_to_string(etat3)

print("Message :", res)
