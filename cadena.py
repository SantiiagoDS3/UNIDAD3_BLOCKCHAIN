import hashlib

data = "Transacccion santiago -> chuy"
prev_hash = "0000"
hash = hashlib.sha256((data + prev_hash).encode()).hexdigest()
print(hash)
