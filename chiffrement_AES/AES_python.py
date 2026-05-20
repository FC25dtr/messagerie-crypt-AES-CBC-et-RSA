import copy  # necessaire pour copier des listes imbriquées sans modifier l originale

# configurations globales de AES
polynome = 0b100011011  # polynome irréductible de GF(2^8), définit les regles de multiplication dans le corps de Galois
c = 0b01100011  # constante de la transformation affine dans SubBytes, définie par la spec AES
matrix_mix_columns = [[2,3,1,1],[1,2,3,1],[1,1,2,3],[3,1,1,2]]  # matrice de MixColumns, les coefficients sont dans GF(2^8)
matrix_invmix_columns = [[0xe,0xb,0xd,0x9],[0x9,0xe,0xb,0xd],[0xd,0x9,0xe,0xb],[0xb,0xd,0x9,0xe]]  # matrice inverse pour le dechiffrement

def tohex(n):  # convertit un entier en string hexadecimale sur 2 caracteres
    if n < 16: return '0'+hex(n)[-1]  # on ajoute un zero devant si < 16 pour toujours avoir 2 caracteres
    else: return hex(n)[2:]

def affiche(L):  # affiche une matrice 4x4 en hexadecimal, utile pour debugger
    print(list(map(tohex,L[0])))
    print(list(map(tohex,L[1])))
    print(list(map(tohex,L[2])))
    print(list(map(tohex,L[3])))
    print()

def convert_to_state(message):  # convertit une string de 16 caracteres en matrice 4x4 pour AES
    state = [0]*4
    for i in range(4):
        state[i] = [ord(message[0:4][i]),ord(message[4:8][i]),ord(message[8:12][i]),ord(message[12:16][i])]  # AES lit les octets par colonnes donc on reorganise ainsi
    return state

def multbyalpha(x):  # multiplication par alpha dans GF(2^8), c est un decalage de bits avec reduction si necessaire
    y = x << 1  # decalage a gauche = multiplication par 2
    if (y & (1 << 8)):  # si le bit 8 est mis il faut reduire par le polynome
        y = y ^ polynome
    return y

def multbygen(x):  # multiplication par le generateur g = alpha + 1
    return (multbyalpha(x)^x)

def construit_F_2_8():  # construit les tables de logarithmes discrets dans GF(2^8) pour accelerer les multiplications
    table = [1]  # table[i] = g^i mod polynome
    log_t = [0]*256
    log_t[0] = -1  # log de 0 est indéfini, on met -1
    log_t[1] = 0  # g^0 = 1 donc log(1) = 0
    for i in range(1,255):
        aux = multbygen(table[i-1])  # on calcule g^i en multipliant g^(i-1) par g
        table = table + [aux]
        log_t[aux] = i  # on stocke le logarithme
    table += [1]  # on boucle, g^255 = g^0 = 1
    return table, log_t

gen, log_gen = construit_F_2_8()  # on construit les tables une seule fois au chargement du module

def mult(a,b):  # multiplication dans GF(2^8) via les tables de log, plus rapide que le calcul direct
    if (a == 0) or (b == 0): return 0  # cas special, 0 * n'importe quoi = 0
    idxa = log_gen[a]
    idxb = log_gen[b]
    return gen[(idxa+idxb) % 255]  # log(a*b) = log(a) + log(b), on cherche l antilog

def multiplication(a, b):  # meme chose que mult, utilisée dans MixColumns
    if a == 0 or b == 0: return 0
    return gen[(log_gen[a] + log_gen[b]) % 255]

def inv(x):  # inverse multiplicatif dans GF(2^8), utilisé dans SubBytes
    if x == 0: return 0  # 0 n a pas d inverse, la spec AES renvoie 0
    idx = log_gen[x]
    return gen[255-idx]  # l inverse de g^i est g^(255-i) car g^255 = 1

def matvecbin(M,R):  # multiplication matrice vecteur en GF(2), utilisée dans la transformation affine de SubBytes
    L = 0
    tmp = R
    res = 0
    for i in range(len(M)):
        for k in range(len(M[i])):
            res = res ^ M[i][k]&(R&1)  # XOR des bits selon la matrice
            R = R >> 1
        R = tmp
        L = L | (res << i)
        res = 0
    return L

def XORliste(b,e):  # XOR entre un vecteur b et un entier e bit par bit, pour la transformation affine
    res = 0
    for i in range(len(b)):
        res = res ^ (((e&1) ^b[i])<<i)
        e = e >>1
    return res

def Subbytes(etat):  # transformation SubBytes, applique la S-Box a chaque octet de l etat
    A = [[1,0,0,0,1,1,1,1],[1,1,0,0,0,1,1,1],[1,1,1,0,0,0,1,1],
         [1,1,1,1,0,0,0,1],[1,1,1,1,1,0,0,0],[0,1,1,1,1,1,0,0],
         [0,0,1,1,1,1,1,0],[0,0,0,1,1,1,1,1]]  # matrice de la transformation affine definie par la spec AES
    b = [1,1,0,0,0,1,1,0]  # vecteur constant de la transformation affine
    resultat = [ligne[:] for ligne in etat]  # copie de l etat pour ne pas modifier l original
    for i in range(len(resultat)):
        for j in range(len(resultat[i])):
            tmp = inv(resultat[i][j])  # on calcule l inverse dans GF(2^8)
            tmp1 = matvecbin(A, tmp)  # on applique la transformation affine
            resultat[i][j] = XORliste(b, tmp1)  # on XOR avec la constante b
    return resultat

def ShiftRows(etat):  # decale les lignes de l etat circulairement vers la gauche
    tmp = etat[0]
    tmp1 = etat[1]
    tmp2 = etat[2]
    tmp3 = etat[3]
    return [tmp, tmp1[1:]+[tmp1[0]], tmp2[2:]+tmp2[:2], tmp3[3:]+tmp3[:3]]  # ligne 0 pas de decalage, ligne 1 decalage de 1, etc

def MixColumns(etat):  # multiplie chaque colonne par la matrice de MixColumns dans GF(2^8)
    matrice = [[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]]
    for k in range(len(etat)):
        for i in range(len(etat)):
            tmp = 0
            for j in range(len(etat)):
                tmp1 = multiplication(matrix_mix_columns[k][j], etat[j][i])  # multiplication dans GF(2^8)
                tmp = tmp ^ tmp1  # addition dans GF(2^8) = XOR
            matrice[k][i] = tmp
    return matrice

def AddRoundKey(etat, tour):  # XOR l etat avec la sous-clé du tour correspondant
    state = []
    K = [0,0,0,0]
    for i in range(4):
        K[i] = W[i][4*tour:4*(tour+1)]  # on extrait les 4 colonnes de la sous-clé du tour depuis W
    for i in range(4):
        aux = []
        for j in range(4):
            aux = aux + [etat[i][j] ^ K[i][j]]  # XOR octet par octet
        state = state + [aux]
    return state

def S(x):  # calcule la S-Box pour une valeur x, utilisée dans le key schedule
    if x == 0:
        y = 0
    else:
        y = inv(x)  # on commence par l inverse dans GF(2^8)
    result = 0
    for i in range(8):
        result = result ^ ((((y >> i) & 1)^((y >>((i+4) % 8)) & 1)^((y >> ((i+5) % 8)) & 1)^((y >> ((i+6) % 8)) & 1)^((y >> ((i+7) % 8)) & 1)^((c >> i) & 1)) << i)  # transformation affine bit par bit
    return result

def gen_cles(k):  # génere les 11 sous-clés AES à partir de la clé principale de 16 caracteres
    global W  # W est globale car AddRoundKey y accede directement sans parametre
    RC = [0,1]
    for i in range(2,11):
        RC = RC + [multbyalpha(RC[i-1])]  # constantes de round, calculées par multiplication successive dans GF(2^8)
    W_ = [[0]*4 for _ in range(44)]  # 44 mots de 4 octets = 11 sous-clés de 16 octets
    cle_convert = convert_to_state(k)  # on convertit la clé en matrice 4x4
    for j in range(4):
        for i in range(4):
            W_[i][j] = cle_convert[j][i]  # on remplit les 4 premiers mots avec la clé
    for i in range(4,44):
        temp = W_[i-1]
        if (i % 4) == 0:
            temp = list(map(S,temp[1:]+[temp[0]]))  # rotation + S-Box sur le mot precedent tous les 4 mots
            temp[0] ^= RC[i//4]  # XOR avec la constante de round
        for j in range(4):
            W_[i][j] = W_[i-4][j] ^ temp[j]  # chaque mot est le XOR du mot 4 positions avant et du temp
    return transforme(W_)

def transforme(W):  # reorganise W pour que AddRoundKey puisse y acceder facilement par ligne
    L=[0]*4
    for i in range(4):
        L[i] = [0]*44
        for j in range(44):
            L[i][j] = W[j][i]
    return L

SBOX = [S(i) for i in range(256)]  # on precalcule toute la S-Box pour eviter de recalculer a chaque SubBytes
INVsbox = [0] * 256
for i in range(256):
    INVsbox[SBOX[i]] = i  # on construit la S-Box inverse pour le dechiffrement

def INVSubbytes(etat):  # SubBytes inverse, utilise la S-Box inverse pour le dechiffrement
    liste = []
    for i in range(4):
        l = []
        for j in range(4):
            l += [INVsbox[etat[i][j]]]  # on applique directement la S-Box inverse precalculée
        liste += [l]
    return liste

def INVShiftRows(etat):  # ShiftRows inverse, decale les lignes vers la droite
    state = [etat[0]]  # ligne 0 inchangée
    state = state + [[etat[1][3]] + etat[1][:3]]  # ligne 1 decalée de 1 vers la droite
    state = state + [etat[2][2:] + etat[2][0:2]]  # ligne 2 decalée de 2
    state = state + [etat[3][1:] + [etat[3][0]]]  # ligne 3 decalée de 3
    return state

def INVMixColumns(etat):  # MixColumns inverse avec la matrice inverse
    state = []
    for i in range(4):
        aux = []
        for j in range(4):
            somme = 0
            for k in range(4):
                somme = somme ^ mult(matrix_invmix_columns[i][k], etat[k][j])  # multiplication avec la matrice inverse dans GF(2^8)
            aux = aux + [somme]
        state = state + [aux]
    return state

def INVAddRoundKey(etat, tour):  # AddRoundKey inverse pour les rounds intermediaires du dechiffrement
    state = []
    K = [0,0,0,0]
    for i in range(4):
        K[i] = W[i][4*tour:4*(tour+1)]
    K = INVMixColumns(K)  # on applique INVMixColumns sur la sous-clé car l ordre des operations est inversé
    for i in range(4):
        aux = []
        for j in range(4):
            aux = aux + [etat[i][j] ^ K[i][j]]
        state = state + [aux]
    return state

def string_to_bytes(etat):  # convertit une string en liste de blocs AES 4x4, ajoute du padding si necessaire
    while len(etat) % 16 != 0:
        etat += '\x00'  # on complete avec des zeros pour avoir un multiple de 16 caracteres
    tab = []
    saut, saut1 = 0, 16
    while len(etat) > saut1:
        tab += [convert_to_state(etat[saut:saut1])]  # on decoupe par blocs de 16 et on convertit en matrice
        saut += 16
        saut1 += 16
    tab += [convert_to_state(etat[saut:])]  # on ajoute le dernier bloc
    return tab

def bytes_to_string(tab):  # convertit une liste de blocs AES 4x4 en string lisible
    res = ""
    for i in range(len(tab)):
        for k in range(4):
            for j in range(4):
                res += chr(tab[i][j][k])  # on lit les octets dans le bon ordre
    return res.rstrip('\x00')  # on retire le padding de zeros ajouté avant le chiffrement

def CBC_chiffrement_aes(message, IV):  # chiffrement AES en mode CBC, chaque bloc est XORé avec le precedent avant chiffrement
    tab = string_to_bytes(message)  # on convertit le message en blocs
    for i in range(len(tab)):
        for j in range(4):
            for k in range(4):
                tab[i][j][k] = tab[i][j][k] ^ IV[j][k]  # XOR avec l IV ou le bloc chiffré precedent
        tab[i] = AddRoundKey(tab[i], 0)  # round initial
        for l in range(1,10):
            tab[i] = Subbytes(tab[i])
            tab[i] = ShiftRows(tab[i])
            tab[i] = MixColumns(tab[i])
            tab[i] = AddRoundKey(tab[i], l)  # 9 rounds complets
        tab[i] = Subbytes(tab[i])
        tab[i] = ShiftRows(tab[i])
        tab[i] = AddRoundKey(tab[i], 10)  # round final sans MixColumns
        IV = tab[i]  # le bloc chiffré devient le nouvel IV pour le bloc suivant
    return tab

def CBC_dechiffrement_aes(tab, IV):  # dechiffrement AES en mode CBC, inverse de CBC_chiffrement_aes
    tab_bis = copy.deepcopy(tab)  # on garde une copie des blocs chiffrés car on en a besoin pour le XOR CBC
    for i in range(len(tab)):
        tab[i] = AddRoundKey(tab[i], 10)  # on commence par le dernier round
        for l in range(9, 0, -1):
            tab[i] = INVSubbytes(tab[i])
            tab[i] = INVShiftRows(tab[i])
            tab[i] = INVMixColumns(tab[i])
            tab[i] = INVAddRoundKey(tab[i], l)  # 9 rounds inverses
        tab[i] = INVSubbytes(tab[i])
        tab[i] = INVShiftRows(tab[i])
        tab[i] = AddRoundKey(tab[i], 0)  # round initial inverse
        prev = IV if i == 0 else tab_bis[i-1]  # pour le premier bloc on XOR avec l IV, sinon avec le bloc chiffré precedent
        for j in range(4):
            for k in range(4):
                tab[i][j][k] = tab[i][j][k] ^ prev[j][k]  # XOR pour annuler le CBC du chiffrement
    res = bytes_to_string(tab)
    return res

W = gen_cles("Ceci est une cle")  # initialisation de W avec une clé par défaut, sera ecrasée par gen_cles() a chaque message
