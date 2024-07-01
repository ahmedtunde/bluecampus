import hashlib

def compute_sha256_hash(input_string):
    sha256_hash = hashlib.sha256()
    
    sha256_hash.update(input_string.encode('utf-8'))
    
    hash_string = sha256_hash.hexdigest()
    
    return hash_string

input_string = "EDVES NIGERIA LIMITED290524"

hash_string = compute_sha256_hash(input_string)

print(f"Result: {hash_string}")
