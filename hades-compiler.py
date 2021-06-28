import json
import os

filename = "Path\To\cfile"
mem_code_start_addr = 0x000
mem_size = 0xFFF
mem_stack_start_addr = 0x7FF


### variables depending on hades.h ###
stack_init_offset = 6
######################################

fname = os.path.splitext(filename)[0]
output_filetype_mif = ".mif"
output_filetype_hix = ".hix"
output_filetype_object = ".o"
output_filetype_asm = ".asm"
depth = 4096
width = 32

def getSection(jsonObj, name):
    for sec in jsonObj["sections"]:
        if sec["name"] == name:
            return sec
    return 0

def getSymbol(jsonObj, id):
    symbol = jsonObj["symbols"][int(id)]
    assert(symbol["id"] == int(id))
    return symbol

def getCodeAsString(jsonObj):
    sec = getSection(jsonObj, "code")
    code = ""
    for line in sec["data"]:
        code += line
    return code

def convertStringCode(code):
    assert(len(code) % 8 == 0)
    words = []
    n = 8
    for index in range(0, len(code), n):
        str_word = code[index : index + n]
        words.append(int(str_word, 16))
    return words

def initStackPointer(code, init_offset, stack_addr):
    code[init_offset] += stack_addr
    return code

def initRel12Relocation(obj, code, relocation):
    reloc_offset = int(relocation["offset"], 16)
    symbol_id = relocation["symbol_id"]
    symbol = getSymbol(obj, symbol_id)  
    symbol_value = int(symbol["value"], 16)
    offset = symbol_value - reloc_offset
    unsigned_offset = (offset // 4) & 0xFFFF
    code[(reloc_offset // 4)] += unsigned_offset

def initRelocations(obj, code):
    for reloc in obj["relocations"]:
        reloc_type = reloc["type"]
        if reloc_type == "rel12":
            initRel12Relocation(obj, code, reloc)
        else:
            raise Exception("Undefined relocation type '{0}'!".format(reloc["type"]))

def insertCodeInImage(image, code, code_start_addr):
    assert(len(image) >= (code_start_addr + len(code)))
    for i in range(code_start_addr, code_start_addr + len(code)):
        image[i] = code[i - code_start_addr]
    return image

def imageToByteArray(image):
    byte_array = []
    for i in image:
        i_bytes = i.to_bytes(4, 'big')
        byte_array.append(i_bytes[0])
        byte_array.append(i_bytes[1])
        byte_array.append(i_bytes[2])
        byte_array.append(i_bytes[3])
    return bytes(byte_array)

def format_mif(bytes, depth=4096, width=32):
    new_line = "\n"
    address_format = "{:04X}"
    new_line_del = ";" + new_line
    mif_content = ""
    mif_content += "DEPTH = " + str(depth) + new_line_del
    mif_content += "WIDTH = " + str(width) + new_line_del
    mif_content += "ADDRESS_RADIX = HEX" + new_line_del
    mif_content += "DATA_RADIX = HEX" + new_line_del
    mif_content += "CONTENT" + new_line
    mif_content += "BEGIN" + new_line
    mif_content += "[0.." + address_format.format(depth - 1) + "] : 0" + new_line_del

    index_format = address_format + ": " 
    word = ""
    for i in range(0, len(bytes)):
        word += "{:02X}".format(bytes[i])
        if (len(word) == width // 4):            
            mif_content += index_format.format(i // 4)
            mif_content += word + new_line_del
            word = ""
    return mif_content

os.system("python -m ppci.cli.cc -m hades {0} -o {1}".format(filename, fname + output_filetype_object))
os.system("python -m ppci.cli.cc -m hades {0} -o {1} -S >nul 2>&1".format(filename, fname + output_filetype_asm))

with open(fname + output_filetype_object) as f:
    obj = json.load(f)

string_code = getCodeAsString(obj)
code = convertStringCode(string_code)
#image = [0 for i in range(mem_size)]
initStackPointer(code, stack_init_offset, mem_stack_start_addr)
initRelocations(obj, code)
#insertCodeInImage(image, code, mem_code_start_addr)
b_image = imageToByteArray(code)

with open(fname + output_filetype_mif, "w") as text_file:
    text_file.write(format_mif(b_image, depth, width))

with open(fname + output_filetype_hix, "wb") as text_file:
    text_file.write(b_image)