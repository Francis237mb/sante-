import struct
import re
import os

def compile_po_to_mo(po_path, mo_path):
    print(f"Compiling {po_path} to {mo_path}...")
    if not os.path.exists(po_path):
        print(f"Error: {po_path} not found.")
        return False
        
    with open(po_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    entries = {}
    msgid = ""
    msgstr = ""
    state = None # 'msgid' or 'msgstr'
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        if line.startswith('msgid '):
            if msgid or msgstr:
                entries[msgid] = msgstr
            msgid = line[6:].strip('"').replace(r'\"', '"').replace(r'\n', '\n')
            msgstr = ""
            state = 'msgid'
        elif line.startswith('msgstr '):
            msgstr = line[7:].strip('"').replace(r'\"', '"').replace(r'\n', '\n')
            state = 'msgstr'
        elif line.startswith('"') and line.endswith('"'):
            content = line[1:-1].replace(r'\"', '"').replace(r'\n', '\n')
            if state == 'msgid':
                msgid += content
            elif state == 'msgstr':
                msgstr += content
                
    if msgid or msgstr:
        entries[msgid] = msgstr

    if not entries:
        print("Warning: No messages found to compile.")
        return False

    magic = 0x950412de
    revision = 0
    num_strings = len(entries)
    
    sorted_keys = sorted(entries.keys())
    
    orig_table_offset = 28
    trans_table_offset = orig_table_offset + 8 * num_strings
    string_data_offset = trans_table_offset + 8 * num_strings
    
    orig_table = []
    trans_table = []
    
    orig_strings_data = b''
    trans_strings_data = b''
    
    current_offset = string_data_offset
    for key in sorted_keys:
        key_bytes = key.encode('utf-8') + b'\x00'
        length = len(key_bytes) - 1
        orig_table.append((length, current_offset))
        orig_strings_data += key_bytes
        current_offset += len(key_bytes)
        
    for key in sorted_keys:
        val_bytes = entries[key].encode('utf-8') + b'\x00'
        length = len(val_bytes) - 1
        trans_table.append((length, current_offset))
        trans_strings_data += val_bytes
        current_offset += len(val_bytes)
        
    # Pack binary header (magic, revision, num_strings, orig_offset, trans_offset, hash_size, hash_offset)
    data = struct.pack('<IIIIIII', magic, revision, num_strings, orig_table_offset, trans_table_offset, 0, 0)
    
    # Pack original table
    for length, offset in orig_table:
        data += struct.pack('<II', length, offset)
        
    # Pack translation table
    for length, offset in trans_table:
        data += struct.pack('<II', length, offset)
        
    # Pack raw strings
    data += orig_strings_data + trans_strings_data
    
    os.makedirs(os.path.dirname(mo_path), exist_ok=True)
    with open(mo_path, 'wb') as f:
        f.write(data)
    print("Success!")
    return True

if __name__ == '__main__':
    # Compile english po to mo
    compile_po_to_mo(
        'locale/en/LC_MESSAGES/django.po', 
        'locale/en/LC_MESSAGES/django.mo'
    )
