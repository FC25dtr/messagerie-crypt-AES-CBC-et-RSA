def pgcd(a,b): # calcul du PGCD avec la méthode d'euclyde
    while b > 0:
        a,b = b,a%b #formule basique tant que b n'est pas null
    return a 

def euclide_e(a,n):
    u = 1 #initialisation de mon aglo ( à voir comme un tableau ou u1 et en dessous de u)
    v = 0
    u1 = 0
    v1 = 1
    while n != 0: #tq le reste de la derniere division n'est pas 0
        q = a//n # calcul du quotient pour l'utiliser dans la formule 
        r = a%n #et du reste pour decaler tout le tableau d'un cran
        a,n = n,r #décalage du tableau
        u,u1 = u1,u - q*u1 #pplication de la formule général 
        v,v1 = v1,v - q*v1
    return [u,v,a] #ici u est le symétrique multiplicatif de n dans a

def inverse(a,p):
    n = p
    if pgcd(a,n) != 1: # controle si l"element est premier avec p c'est à dire qu'il possède un symétrique dans Z/pZ
        print("votre nombre ne possède pas de symétrique ici")
        return None
    L = euclide_e(a, p) #j'applique euclyde etendu et recupere seulement l'element symetrique 
    return L[0] % n #retour du symetrique, %n au cas ou il est negatif 

def decompose(n): #décompose en produit de facteur premier
    L = [] #liste qui contiendra la decomposition
    j = 0
    if n % 2 == 0: # je compte si divisible par deux et combien de fois il l'est
        while n%2 == 0:
            j+=1
            n = n // 2 #je divise par deux comme il est divisible
        L = L + [[2,j]] #j'ajoute à ma liste de decomposition en produit de facteur premier 
    i = 3 # en partant de i = 3 et en faisant des saut de 2
    while i*i <= n:
        j = 0
        if n % i == 0:
            while n%i == 0: # meme methode que pour deux mais la on le fait sur i
                j+=1
                n = n // i 
            L = L + [[i,j]]
        i += 2 
    if n > 1:
        L = L + [[n, 1]] #si il ne se decompose pas plus mais superieur à 1 on rajoute l'element 
    return L

def euler_phi(n): #calcul de phi avec l'aide de la decompo
    L = decompose(n)
    s = 1
    for i in range(len(L)):
        s *= L[i][0]**L[i][1] - L[i][0]**(L[i][1]-1) #regle de calcul de phi à l'aide de la decompo 
    return s 

def ord(a, p): # calcul de l'ordre multiplicatif dans p
    a %= p # au cas ou a > p
    if a == 0: 
        return 0
    n = p - 1 #par du principe que l'ordre divise p-1
    i = 1
    best = n
    while i * i <= n: #complexite de racine de n
        if n % i == 0: # si divisible par p-1
            if pow(a, i, p) == 1: # teste si a**i donne 1
                return i # ici je suis sur que c'est le plus petit donc je le retourne 
            j = n // i #je teste l'autre element divisible par p-1
            if pow(a, j, p) == 1 and j < best: # pareil pour j
                best = j # retourne pas directement car pas forcement le plus petit j qui donne 1
        i += 1
    return best # retour de l'ordre si supérieur à la racine 



def Exponentiation(a,b,n):
    resultat = pow(a,b,n) # methode la plus rapide pour caluler une puissance dans un espace modulaire
    return resultat 

def decompose_for_miller_rabin(n): # decomposition special pour miller rabin
    d = n - 1
    s = 0
    while d % 2 == 0:  # tant que d est pair
        d //= 2         # division entière par 2
        s += 1          # compter le nombre de facteurs 2
    return s, d
    
