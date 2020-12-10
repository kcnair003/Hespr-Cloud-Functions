from google.cloud import firestore
import base64
from Crypto.Cipher import AES
from Crypto import Random
from Crypto.Protocol.KDF import PBKDF2
import traceback
import re
import string

BLOCK_SIZE = 16
pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * chr(BLOCK_SIZE - len(s) % BLOCK_SIZE)
unpad = lambda s: s[:-ord(s[len(s) - 1:])]

db = firestore.Client()

def get_private_key(password):
    salt = b"this is a salt"
    kdf = PBKDF2(password, salt, 64, 1000)
    key = kdf[:32]
    return key
 
 
def encrypt(raw, password):
    private_key = get_private_key(password)
    raw = pad(raw)
    iv = Random.new().read(AES.block_size)
    cipher = AES.new(private_key, AES.MODE_CBC, iv)
    return base64.b64encode(iv + cipher.encrypt(raw))
 
 
def decrypt(enc, password):
    private_key = get_private_key(password)
    enc = base64.b64decode(enc)
    iv = enc[:16]
    cipher = AES.new(private_key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(enc[16:]))

def encrypt_information(journal_ref):
    journal_text = ""
    journalBytes = b""
    journal_dict = journal_ref.get().to_dict()
    try:
        key_b64 = journal_dict['key']
        journal_text_intermediate = journal_dict['journal_text']
        journal_text = journal_text_intermediate.replace("’", "\\").replace("'", "\\")
    except Exception as e:
        print("An error occurred with finding the journal text")
        traceback.print_exc()
    try:
        journalBytes = encrypt(journal_text, key_b64)
        data = {'journal_text': journalBytes}
        journal_ref.update(data)
    except Exception as e:
        print('An error occurred encrypting the journal')
        traceback.print_exc()
    return journal_text

def decrypt_information(journal_ref):
    decodedText = ""
    journalBytes = b""
    try:
        entryBytesDict = journal_ref.get().to_dict()
        entryBytesText = entryBytesDict['journal_text']
        key_b64 = entryBytesDict['key']
        entryBytes = decrypt(entryBytesText, key_b64)
        decodedTextIntermediate = bytes.decode(entryBytes)
        decodedText = decodedTextIntermediate.replace("\\", "'")
    except Exception as e:
        print('An error occurred with decrypting the journal')
        traceback.print_exc()
    try:
        data = {'key': firestore.DELETE_FIELD}
        journal_ref.update(data)
    except Exception as e:
        traceback.print_exc()
    return decodedText

def processEncryptedData(request):
    """Responds to any HTTP request.
    Args:
        request (flask.Request): HTTP request object.
    Returns:
        The response text or any set of values that can be turned into a
        Response object using
        `make_response <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>`.
    """
    request_json = request.get_json()
    if request.args and 'journal_ref' in request.args:
        encrypt_information(request.args.get('journal_ref'))
        return decrypt_information(request.args.get('journal_ref'))
    elif request_json and 'journal_ref' in request_json:
        encrypt_information(request_json['journal_ref'])
        return decrypt_information(request_json['journal_ref'])
    else:
        return f'Decryption is not possible!'
