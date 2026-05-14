import socket 

s = socket.socket()
s.bind(('localhost',5001))
s.listen(2)  
conn_bob, addr_bob = s.accept() 
conn_alice, addr_alice = s.accept()
cle_pub_bob = conn_bob.recv(1024)  
conn_alice.send(cle_pub_bob)
message_alice = conn_alice.recv(1024)
conn_bob.send(message_alice) 
conn_bob.close()
conn_alice.close()
s.close()