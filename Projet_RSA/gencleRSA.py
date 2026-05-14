import random 
from . import math_utile
def miller_rabbin(n,k): #teste si un rand nombre est premier avec k testes 
    if n < 2: # forcement pas premier 
        return False
    if n == 2 or n == 3: # forcement premier 
        return True 
    if n%2 == 0: #forcement pas premier 
        return False 
    (s,d) = math_utile.decompose_for_miller_rabin(n)
    for i in range(k): #pour effectuer exacteement k testes
        a = random.randrange(2,n-2) #genere aleatoire pour le teste
        x = math_utile.Exponentiation(a,d,n)  #puissance modulaire
        if x == 1 or x == n-1: # #teste 1 validé si 
            continue
        for j in range(s-1): # je cntinue les testes 
            x = (x*x)% n
            if x == n-1:
                break
            elif x == 1:
                return False 
        if x != n-1:
            return False 
    return True #renvoie True si tout les testes sont passé

def gencle_RSAA(): #je genere les cle RSA 
    i = 0
    L = []
    while i < 2:
        a = random.randint(1,2**512) #genere un entier sur max 512 bits 
        if miller_rabbin(a, 7): #teste la primalite 
            i += 1
            L += [a]
    p,q = L[0],L[1]# je definie p e tq avec les deux nombres premiers
    if p == q:
        print("restart")
        return gencle_RSAA()
    n = p * q #je definie n
    id_euler = (p-1)*(q-1) # je trouve phi de n
    e = 65537
    if math_utile.pgcd(id_euler, e) != 1:
        print("restart")
        return gencle_RSAA() 
    d = math_utile.inverse(e,id_euler)
    if (e*d)%id_euler !=1: #teste si d*e est bien 
        print("error")
        return None
    cle_pub = (n,e) #je cree les cles publique et privé 
    cle_priv = (n,d)
    return cle_pub,cle_priv,n
    
    
def message_vers_entier(message):
    m = 0
    for c in message:
        m = m * 256 + ord(c)  # décale le bloc et ajoute le nouveau caractère
    return m #pour executer ou non

def taille_max_bloc(n):
    k = 0
    puissance = 1
    while puissance * 256 < n:
        puissance *= 256 #tant que la puissance est inferieur a n ej rajoute 1 au max 
        k += 1
    return k

def message_en_blocs(message, n):
    bloc_taille = taille_max_bloc(n) #je definie la taille max 
    blocs = []
    for i in range(0, len(message), bloc_taille): # je saute de bloc en bloque
        bloc = message[i:i + bloc_taille] #tout ceux qu'il y a entre
        blocs.append(message_vers_entier(bloc)) # je creer le codage bloc par bloc 
    return blocs

def chiffrement_blocs(cle_publique, message):
    n, e = cle_publique 
    blocs = message_en_blocs(message, n)
    blocs_chiffres = [] #j'initialise la liste des pluesieurs blocs
    for bloc in blocs:
        chiffre = math_utile.Exponentiation(bloc, e, n)
        blocs_chiffres.append(chiffre) #dechiffrement total des blocs
    return blocs_chiffres

def dechiffrement_blocs(cle_privee, blocs_chiffres):
    n, d = cle_privee
    message = ""
    for bloc_chiffre in blocs_chiffres:
        bloc = math_utile.Exponentiation(bloc_chiffre, d, n)
        message += entier_vers_texte(bloc) #dechiffrement total des blocs
    return message #retour du message total


def entier_vers_texte(m):
    caracteres = []
    while m > 0:
        code = m % 256 # récupérer le code du dernier caractère
        caracteres.append(chr(code))
        m = m // 256 # avancer vers le caractère précédent
    caracteres.reverse() # inverser la liste pour retrouver l'ordre original
    return "".join(caracteres)

def RSA(): #utilisation de toutes les fonctions
    cle_pub, cle_priv,n = gencle_RSAA()
    print("Clés publiques :", cle_pub)
    print("Clés privées :", cle_priv)
    message = input("Entrez un message : ")
    print("Message original :", message)
    # Chiffrement
    blocs_chiffres = chiffrement_blocs(cle_pub, message)
    print("Message chiffré :", blocs_chiffres)
    # Déchiffrement
    message_dechiffre = dechiffrement_blocs(cle_priv, blocs_chiffres)
    print("Message déchiffré :", message_dechiffre)
    print("la taille est : ",n)
    return message_dechiffre
