import hashlib

print("Ana:", hashlib.sha256("password123".encode()).hexdigest())
print("Luis:", hashlib.sha256("admin456".encode()).hexdigest())
