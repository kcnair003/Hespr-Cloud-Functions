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

def encrypt_information(event, context):
    """Triggered by a change to a Firestore document.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    resource_string = context.resource
    # print out the resource string that triggered the function
    print(f"Function triggered by change to: {resource_string}.")
    # now print out the entire event object
    print(str(event))
    resource_string_list = resource_string.split('/')
    journal_id = resource_string_list[6]
    print(journal_id)
    value_dict = event['value']
    # Defines the dictionary associated the 'fields' key
    fields_dict = value_dict['fields']
    # Defines the dictionaries associated with the keys 'journal_text' and 'timestamp'
    journal_text = ""
    journalBytes = b""
    journal_ref = db.collection(u'test_guided_journals').document(journal_id)
    try:
        key_b64_dict = fields_dict['key']
        key_b64 = key_b64_dict['stringValue']
        journal_text_dict = fields_dict['journal_text']
        journal_text_intermediate = journal_text_dict['stringValue']
        print(journal_text_intermediate)
        journal_text = journal_text_intermediate.replace("’", "\\").replace("'", "\\")
        print(journal_text)
    except Exception as e:
        print("An error occurred with finding the journal text")
        traceback.print_exc()
    try:
        journalBytes = encrypt(journal_text, key_b64)
        print(journalBytes)
        data = {'journal_text': journalBytes}
        journal_ref.update(data)
    except Exception as e:
        print('An error occurred encrypting the journal')
        traceback.print_exc()
    try:
        specificBytes = decrypt(journalBytes, key_b64)
        print(bytes.decode(specificBytes))
        entryBytesDict = journal_ref.get().to_dict()
        entryBytesText = entryBytesDict['journal_text']
        entryBytes = decrypt(entryBytesText, key_b64)
        print(bytes.decode(entryBytes))
    except Exception as e:
        print('An error occurred with decrypting the journal')
        traceback.print_exc()
