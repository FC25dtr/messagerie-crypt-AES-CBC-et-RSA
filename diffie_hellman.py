p = 0xFFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E088A67CC74020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7EDEE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3DC2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F83655D23DCA3AD961C62F356208552BB9ED529077096966D670C354E4ABC9804F1746C08CA18217C32905E462E36CE3BE39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9DE2BCBF6955817183995497CEA956AE515D2261898FA051015728E5A8AACAA68FFFFFFFFFFFFFFFF  # nombre premier de 2048 bits standardisé par le RFC 3526, groupe DH-2048, ce nombre est public et reconnu comme sur
g = 2  # générateur du groupe, valeur standard, g=2 est le plus utilisé

import random  # pour générer la clé privée aléatoire

def generer_cle_dh():  # génere une paire de clés pour l echange DH
    a = random.randint(2, p-2)  # clé privée secrète, jamais envoyée sur le réseau
    A = pow(g, a, p)  # clé publique calculée A = g^a mod p, c est cette valeur qu on envoie a l autre
    return a, A

def calculer_cle_commune(a, B):  # calcule la clé commune a partir de notre clé privée et la valeur publique reçue
    return pow(B, a, p)  # donne g^(ab) mod p, identique des deux cotés grace aux propriétés de l arithmétique modulaire
