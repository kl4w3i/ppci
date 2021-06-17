from ..encoding import Instruction, Syntax, Operand
from ..generic_instructions import ArtificialInstruction, Global
from ..isa import Isa, Relocation
from ..token import Token, bit_range
from .registers import HadesRegister
from . import registers

class OpcodeToken(Token):
    class Info:
        size = 32
    aluopcode = bit_range(23, 28)
    opcode = bit_range(28, 32)

class Imm12Token(Token):
    class Info:
        size = 32
    imm = bit_range(0, 12)
    i = bit_range(14, 16)
    imminst = bit_range(16, 17)
    a = bit_range(17, 20)
    wb = bit_range(20, 23)
    aluopcode = bit_range(23, 28)
    opcode = bit_range(28, 32)

class Imm16Token(Token):
    class Info:
        size = 32
    imm = bit_range(0, 16)
    imminst = bit_range(16, 17)
    a = bit_range(17, 20)
    wb = bit_range(20, 23)
    aluopcode = bit_range(23, 28)
    opcode = bit_range(28, 32)

class GetSwiToken(Token):
    class Info:
        size = 32
    i1 = bit_range(0, 1)
    imminst = bit_range(16, 17)
    w = bit_range(20, 23)
    aluopcode = bit_range(23, 28)
    opcode = bit_range(28, 32)

class ALUToken(Token):
    class Info:
        size = 32
    b = bit_range(13, 16)
    a = bit_range(17, 20)
    w = bit_range(20, 23)
    aluopcode = bit_range(23, 28)

class ALUIToken(Token):
    class Info:
        size = 32
    imm = bit_range(0, 16)
    imminst = bit_range(16, 17)
    a = bit_range(17, 20)
    w = bit_range(20, 23)
    aluopcode = bit_range(23, 28)
 
class Abs16Relocation(Relocation):
    name = 'abs16'
    token = Imm12Token
    field = 'label'
    def calc(self, symbol_value, reloc_value):
        return symbol_value

isa = Isa()

class HadesInstruction(Instruction):
    isa = isa

def make_alu(mnemonic, aluopcode):
    w = Operand("w", HadesRegister, write=True)
    a = Operand("a", HadesRegister, read=True)
    b = Operand("b", HadesRegister, read=True)
    syntax = Syntax([mnemonic, " ", w, ",", " ", a, ",", " ", b])
    patterns = {
        "aluopcode": aluopcode,
        "w": w,
        "a": a,
        "b": b,
    }
    members = {
        "tokens": [ALUToken],
        "w": w,
        "a": a,
        "b": b,
        "syntax": syntax,
        "patterns": patterns,
    }
    return type(mnemonic.title(), (HadesInstruction,), members)

def make_alui(mnemonic, aluopcode):
    w = Operand("w", HadesRegister, write=True)
    a = Operand("a", HadesRegister, read=True)
    imm = Operand("imm", int)
    syntax = Syntax([mnemonic, " ", w, ",", " ", a, ",", " ", "#", imm])
    patterns = {
        "aluopcode": aluopcode,
        "w": w,
        "a": a,
        "imm": imm
    }
    members = {
        "tokens": [ALUIToken],
        "w": w,
        "a": a,
        "imm": imm,
        "imminst": 1,
        "syntax": syntax,
        "patterns": patterns,
    }
    return type(mnemonic.title(), (HadesInstruction,), members)


Shl = make_alu("shl", 4)
Shr = make_alu("shr", 5)
Cshl = make_alu("cshl", 6)
Cshr = make_alu("cshr", 7)
And = make_alu("and", 8)
Or = make_alu("or", 9)
Xor = make_alu("xor", 10)
Xnor = make_alu("xnor", 11)
Sub = make_alu("sub", 16)
Add = make_alu("add", 17)
Setov = make_alu("setov", 18)
Getov = make_alu("getov", 19)
Mul = make_alu("mul", 20)
Sne = make_alu("sne", 24)
Seq = make_alu("seq", 25)
Sgt = make_alu("sgt", 26)
Sge = make_alu("sge", 27)
Slt = make_alu("slt", 28)
Sle = make_alu("sle", 29)

Shli = make_alui("shli", 4)
Shri = make_alui("shri", 5)
Cshli = make_alui("cshli", 6)
Cshri = make_alui("cshri", 7)
Andi = make_alui("andi", 8)
Ori = make_alui("ori", 9)
Xori = make_alui("xori", 10)
Xnori = make_alui("xnori", 11)
Subi = make_alui("subi", 16)
Addi = make_alui("addi", 17)
Setovi = make_alui("setovi", 18)
Muli = make_alui("muli", 20)
Snei = make_alui("snei", 24)
Seqi = make_alui("seqi", 25)
Sgti = make_alui("sgti", 26)
Sgei = make_alui("sgei", 27)
Slti = make_alui("slti", 28)
Slei = make_alui("slei", 29)

class Nop(HadesInstruction):
    syntax = Syntax(['nop'])
    tokens = [OpcodeToken]

class Swi(HadesInstruction):
    a = Operand('a', HadesRegister, read=True)
    imm = Operand('imm', int)
    syntax = Syntax(['swi', ' ', a, ',', ' ', '#', imm])
    tokens = [Imm16Token]
    patterns = {
        'aluopcode': 2,
        'a': a,
        'imminst': 1,
        'imm': imm
    }

class GetSwi(HadesInstruction):
    w = Operand('w', HadesRegister, write=True)
    i1 = Operand('i1', int)
    syntax = Syntax(['getswi', ' ', w, ',', ' ', '#', i1])
    tokens = [GetSwiToken]
    patterns = {
        'aluopcode': 3,
        'w': w,
        'imminst': 1,
        'i1': i1
    }

class In(HadesInstruction):
    w = Operand('w', HadesRegister, write=True)
    imm = Operand('imm', int)
    syntax = Syntax(['in', ' ', w, ',', ' ', '#', imm])
    tokens = [Imm16Token]
    patterns = {
        'aluopcode': 14,
        'opcode': 2,
        'wb': w,
        'imminst': 1,
        'imm': imm
    }

class Out(HadesInstruction):
    b = Operand('b', HadesRegister, write=True)
    imm = Operand('imm', int)
    syntax = Syntax(['in', ' ', b, ',', ' ', '#', imm])
    tokens = [Imm16Token]
    patterns = {
        'aluopcode': 14,
        'opcode': 3,
        'wb': b,
        'imminst': 1,
        'imm': imm
    }

class Eni(HadesInstruction):
    syntax = Syntax(['eni'])
    tokens = [OpcodeToken]
    patterns = {
        'opcode': 1
    }

class Dei(HadesInstruction):
    syntax = Syntax(['dei'])
    tokens = [OpcodeToken]
    patterns = {
        'opcode': 4
    }

class Bnez(HadesInstruction):
    a = Operand('a', HadesRegister, read=True)
    imm = Operand('imm', int)
    syntax = Syntax(['bnez', ' ', a, ',', ' ', '#', imm])
    tokens = [Imm12Token]
    patterns = {
        'opcode': 5,
        'aluopcode': 12,
        'a': a,
        'imminst': 1,
        'imm': imm
    }

class Beqz(HadesInstruction):
    a = Operand('a', HadesRegister, read=True)
    imm = Operand('imm', int)
    syntax = Syntax(['beqz', ' ', a, ',', ' ', '#', imm])
    tokens = [Imm12Token]
    patterns = {
        'opcode': 6,
        'aluopcode': 13,
        'a': a,
        'imminst': 1,
        'imm': imm
    }

class Bov(HadesInstruction):
    imm = Operand('imm', int)
    syntax = Syntax(['bov', ' ', '#', imm])
    tokens = [Imm12Token]
    patterns = {
        'opcode': 7,
        'aluopcode': 14,
        'imminst': 1,
        'imm': imm
    }

class Load(HadesInstruction):
    w = Operand('w', HadesRegister, write=True)
    a = Operand('a', HadesRegister, read=True)
    imm = Operand('imm', int)
    syntax = Syntax(['load', ' ', w, ',', ' ', a, ',', ' ', '#', imm])
    tokens = [Imm16Token]
    patterns = {
        'opcode': 8,
        'aluopcode': 17,
        'wb': w,
        'a': a,
        'imminst': 1,
        'imm': imm
    }

class Store(HadesInstruction):
    b = Operand('b', HadesRegister, read=True)
    a = Operand('a', HadesRegister, read=True)
    imm = Operand('imm', int)
    syntax = Syntax(['store', ' ', b, ',', ' ', a, ',', ' ', '#', imm])
    tokens = [Imm16Token]
    patterns = {
        'opcode': 9,
        'aluopcode': 17,
        'wb': b,
        'a': a,
        'imminst': 1,
        'imm': imm
    }

class Jal(HadesInstruction):
    w = Operand('w', HadesRegister, write=True)
    label = Operand('label', str)
    syntax = Syntax(['jal', ' ', w, ',', ' ', '*', label])
    tokens = [Imm12Token]
    patterns = {
        'opcode': 10,
        'aluopcode': 14,
        'wb': w,
        'imminst': 1
    }

    def reloactions(self):
        return [Abs16Relocation(self.label, offset=1)]

class Jreg(HadesInstruction):
    a = Operand('a', HadesRegister, read=True)
    syntax = Syntax(['jreg', ' ', a])
    tokens = [Imm16Token]
    patterns = {
        'opcode': 11,
        'aluopcode': 6,
        'a': a
    }

class Reti(HadesInstruction):
    syntax = Syntax(['reti'])
    tokens = [OpcodeToken]
    patterns = {
        'opcode': 12
    }

class Sisa(HadesInstruction):
    i = Operand('i', int)
    imm = Operand('imm', int)
    syntax = Syntax(['sisa', ' ', i, ',', ' ', '#', imm])
    tokens = [Imm12Token]
    patterns = {
        'opcode': 13,
        'aluopcode': 14,
        'imminst': 1,
        'i': i,
        'imm': imm
    }

class Dpma(HadesInstruction):
    syntax = Syntax(['dpma'])
    tokens = [OpcodeToken]
    patterns = {
        'opcode': 14
    }

class Epma(HadesInstruction):
    syntax = Syntax(['epma'])
    tokens = [OpcodeToken]
    patterns = {
        'opcode': 15
    }

def mov(dst, src):
    return Addi(dst, src, 0)

def ldi(dst, imm):
    return Addi(dst, registers.r0, imm)

def ldui(dst, imm):
    return Ori(dst, registers.r0, imm)

def inc(reg):
    return Addi(reg, reg, 1)

def dec(reg):
    return Subi(reg, reg, 1)

def jmp(imm):
    return Beqz(registers.r0, imm)

def push(reg):
    return (Store(reg, registers.sp, 0) + Addi(registers.sp, registers.sp, 1))

def pop(reg):
    return (Load(reg, registers.sp, -1) + Subi(registers.sp, registers.sp, 1))


# Arithmatic patterns:
@isa.pattern("reg", "ADDI32(reg, reg)", size=4, cycles=1, energy=1)
@isa.pattern("reg", "ADDU32(reg, reg)", size=4, cycles=1, energy=1)
@isa.pattern("reg", "ADDI16(reg, reg)", size=4, cycles=1, energy=1)
@isa.pattern("reg", "ADDU16(reg, reg)", size=4, cycles=1, energy=1)
@isa.pattern("reg", "ADDI8(reg, reg)", size=4, cycles=1, energy=1)
@isa.pattern("reg", "ADDU8(reg, reg)", size=4, cycles=1, energy=1)
def pattern_addi32(context, tree, c0, c1):
    d = context.new_reg(HadesRegister)
    context.emit(Add(d, c1, c0))
    return d


@isa.pattern("reg", "SUBI32(reg, reg)", size=4, cycles=1, energy=1)
@isa.pattern("reg", "SUBU32(reg, reg)", size=4, cycles=1, energy=1)
def pattern_subi32(context, tree, c0, c1):
    d = context.new_reg(HadesRegister)
    context.emit(Sub(d, c1, c0))
    return d


@isa.pattern("reg", "NEGI32(reg)", size=4, cycles=1, energy=1)
def pattern_neg_i32(context, tree, c0):
    d = context.new_reg(HadesRegister)
    context.emit(Sub(d, registers.r0, c0))
    return d


@isa.pattern("reg", "ANDI8(reg, reg)", size=4, cycles=1, energy=1)
@isa.pattern("reg", "ANDU8(reg, reg)", size=4, cycles=1, energy=1)
@isa.pattern("reg", "ANDI16(reg, reg)", size=4, cycles=1, energy=1)
@isa.pattern("reg", "ANDU16(reg, reg)", size=4, cycles=1, energy=1)
@isa.pattern("reg", "ANDI32(reg, reg)", size=4, cycles=1, energy=1)
@isa.pattern("reg", "ANDU32(reg, reg)", size=4, cycles=1, energy=1)
def pattern_and32(context, tree, c0, c1):
    d = context.new_reg(HadesRegister)
    context.emit(And(d, c1, c0))
    return d


@isa.pattern("reg", "ORI8(reg, reg)", size=4, cycles=1, energy=1)
@isa.pattern("reg", "ORU8(reg, reg)", size=4, cycles=1, energy=1)
@isa.pattern("reg", "ORI16(reg, reg)", size=4, cycles=1, energy=1)
@isa.pattern("reg", "ORU16(reg, reg)", size=4, cycles=1, energy=1)
@isa.pattern("reg", "ORI32(reg, reg)", size=4, cycles=1, energy=1)
@isa.pattern("reg", "ORU32(reg, reg)", size=4, cycles=1, energy=1)
def pattern_or32(context, tree, c0, c1):
    d = context.new_reg(HadesRegister)
    context.emit(Or(d, c1, c0))
    return d


@isa.pattern("reg", "XORI32(reg, reg)", size=4, cycles=1, energy=1)
@isa.pattern("reg", "XORU32(reg, reg)", size=4, cycles=1, energy=1)
def pattern_xor32(context, tree, c0, c1):
    d = context.new_reg(HadesRegister)
    context.emit(Xor(d, c1, c0))
    return d


@isa.pattern("reg", "SHLI32(reg, reg)", size=4, cycles=1, energy=1)
@isa.pattern("reg", "SHLU32(reg, reg)", size=4, cycles=1, energy=1)
def pattern_shl(context, tree, c0, c1):
    d = context.new_reg(HadesRegister)
    context.emit(Shl(d, c1, c0))
    return d


@isa.pattern("reg", "SHRI32(reg, reg)", size=4, cycles=1, energy=1)
@isa.pattern("reg", "SHRU32(reg, reg)", size=4, cycles=1, energy=1)
def pattern_shr(context, tree, c0, c1):
    d = context.new_reg(HadesRegister)
    context.emit(Shr(d, c1, c0))
    return d

@isa.pattern("reg", "MULI32(reg, reg)", size=4, cycles=1, energy=1)
@isa.pattern("reg", "MULU32(reg, reg)", size=4, cycles=1, energy=1)
def pattern_mul(context, tree, c0, c1):
    d = context.new_reg(HadesRegister)
    context.emit(Mul(d, c1, c0))
    return d

@isa.pattern("reg", "DIVI32(reg, reg)", size=4, cycles=1, energy=1)
@isa.pattern("reg", "DIVU32(reg, reg)", size=4, cycles=1, energy=1)
def pattern_dev(context, tree, c0, c1):
    # TODO
    return registers.r0


# Memory patterns:
@isa.pattern("mem", "reg", size=0, cycles=0, energy=0)
def pattern_reg_as_mem(context, tree, c0):
    return c0, 0

@isa.pattern("mem", "FPRELU32", size=0, cycles=0, energy=0)
@isa.pattern("mem", "FPRELU16", size=0, cycles=0, energy=0)
def pattern_fprel32(context, tree):
    offset = tree.value.offset
    base = registers.fp
    return base, offset

@isa.pattern("stm", "STRI32(mem, reg)", size=4, cycles=1, energy=1)
@isa.pattern("stm", "STRU32(mem, reg)", size=4, cycles=1, energy=1)
@isa.pattern("stm", "STRI16(mem, reg)", size=4, cycles=1, energy=1)
@isa.pattern("stm", "STRU16(mem, reg)", size=4, cycles=1, energy=1)
@isa.pattern("stm", "STRI8(mem, reg)", size=4, cycles=1, energy=1)
@isa.pattern("stm", "STRU8(mem, reg)", size=4, cycles=1, energy=1)
def pattern_str_32(context, tree, c0, c1):
    base, offset = c0
    context.emit(Store(c1, base, offset))


@isa.pattern("reg", "LDRI32(mem)", size=4, cycles=1, energy=1)
@isa.pattern("reg", "LDRU32(mem)", size=4, cycles=1, energy=1)
@isa.pattern("reg", "LDRI16(mem)", size=4, cycles=1, energy=1)
@isa.pattern("reg", "LDRU16(mem)", size=4, cycles=1, energy=1)
@isa.pattern("reg", "LDRI8(mem)", size=4, cycles=1, energy=1)
@isa.pattern("reg", "LDRU8(mem)", size=4, cycles=1, energy=1)
def pattern_ldr_32(context, tree, c0):
    d = context.new_reg(HadesRegister)
    base, offset = c0
    context.emit(Load(d, base, offset))
    return d


# Misc patterns:
@isa.pattern("stm", "MOVI32(reg)", size=4, cycles=1, energy=1)
@isa.pattern("stm", "MOVU32(reg)", size=4, cycles=1, energy=1)
@isa.pattern("stm", "MOVI16(reg)", size=4, cycles=1, energy=1)
@isa.pattern("stm", "MOVU16(reg)", size=4, cycles=1, energy=1)
@isa.pattern("stm", "MOVI8(reg)", size=4, cycles=1, energy=1)
@isa.pattern("stm", "MOVU8(reg)", size=4, cycles=1, energy=1)
def pattern_mov32(context, tree, c0):
    d = tree.value
    context.emit(mov(d, c0))


@isa.pattern("reg", "CONSTI32", size=8, cycles=2, energy=2)
@isa.pattern("reg", "CONSTU32", size=8, cycles=2, energy=2)
def pattern_const32(context, tree):
    value = tree.value
    upper = (value >> 16) & 0xFFFF
    lower = value & 0xFFFF
    d = context.new_reg(HadesRegister)
    context.emit(ldi(d, upper))
    context.emit(Shli(d, d, 16))
    context.emit(Ori(d, d, lower))
    return d


@isa.pattern("reg", "CONSTI16", size=4, cycles=1, energy=1)
@isa.pattern("reg", "CONSTU16", size=4, cycles=1, energy=1)
@isa.pattern("reg", "CONSTI8", size=4, cycles=1, energy=1)
@isa.pattern("reg", "CONSTU8", size=4, cycles=1, energy=1)
def pattern_const16(context, tree):
    value = tree.value & 0xFFFF
    d = context.new_reg(HadesRegister)
    context.emit(ldi(d, value))
    return d


@isa.pattern("reg", "REGI32", size=0, cycles=0, energy=0)
@isa.pattern("reg", "REGU32", size=0, cycles=0, energy=0)
@isa.pattern("reg", "REGI16", size=0, cycles=0, energy=0)
@isa.pattern("reg", "REGU16", size=0, cycles=0, energy=0)
@isa.pattern("reg", "REGI8", size=0, cycles=0, energy=0)
@isa.pattern("reg", "REGU8", size=0, cycles=0, energy=0)
def pattern_reg(context, tree):
    return tree.value


@isa.pattern("reg", "I32TOI16(reg)", size=0, cycles=0, energy=0)
@isa.pattern("reg", "I32TOU16(reg)", size=0, cycles=0, energy=0)
@isa.pattern("reg", "I32TOI8(reg)", size=0, cycles=0, energy=0)
@isa.pattern("reg", "I32TOU8(reg)", size=0, cycles=0, energy=0)
@isa.pattern("reg", "U32TOI16(reg)", size=0, cycles=0, energy=0)
@isa.pattern("reg", "U32TOU16(reg)", size=0, cycles=0, energy=0)
@isa.pattern("reg", "U32TOI8(reg)", size=0, cycles=0, energy=0)
@isa.pattern("reg", "U32TOU8(reg)", size=0, cycles=0, energy=0)
def pattern_cast(context, tree, c0):
    return c0

@isa.pattern("reg", "I16TOI32(reg)", size=0, cycles=0, energy=0)
@isa.pattern("reg", "I16TOU32(reg)", size=0, cycles=0, energy=0)
@isa.pattern("reg", "I16TOI8(reg)", size=0, cycles=0, energy=0)
@isa.pattern("reg", "I16TOU8(reg)", size=0, cycles=0, energy=0)
@isa.pattern("reg", "U16TOI32(reg)", size=0, cycles=0, energy=0)
@isa.pattern("reg", "U16TOU32(reg)", size=0, cycles=0, energy=0)
@isa.pattern("reg", "U16TOI8(reg)", size=0, cycles=0, energy=0)
@isa.pattern("reg", "U16TOU8(reg)", size=0, cycles=0, energy=0)
def pattern_cast(context, tree, c0):
    return c0

@isa.pattern("reg", "I8TOI32(reg)", size=0, cycles=0, energy=0)
@isa.pattern("reg", "I8TOU32(reg)", size=0, cycles=0, energy=0)
@isa.pattern("reg", "I8TOI16(reg)", size=0, cycles=0, energy=0)
@isa.pattern("reg", "I8TOU16(reg)", size=0, cycles=0, energy=0)
@isa.pattern("reg", "U8TOI32(reg)", size=0, cycles=0, energy=0)
@isa.pattern("reg", "U8TOU32(reg)", size=0, cycles=0, energy=0)
@isa.pattern("reg", "U8TOI16(reg)", size=0, cycles=0, energy=0)
@isa.pattern("reg", "U8TOU16(reg)", size=0, cycles=0, energy=0)
def pattern_cast(context, tree, c0):
    return c0

@isa.pattern("reg", "LABEL", size=8, cycles=2, energy=2)
def pattern_label(context, tree):
    label = tree.value
    d = context.new_reg(HadesRegister)
    context.emit(mov(d, label))
    return d


# Jump
jump_opnames = {"<": Slt, ">": Sgt, "==": Seq, "!=": Sne, ">=": Sge, "<=": Sle}

@isa.pattern("stm", "JMP", size=4)
def pattern_jmp(context, tree):
    tgt = tree.value
    context.emit(Jal(registers.ra, tgt.name, jumps=[tgt]))


@isa.pattern("stm", "CJMPI32(reg, reg)")
@isa.pattern("stm", "CJMPI8(reg, reg)")
@isa.pattern("stm", "CJMPU8(reg, reg)")
def pattern_cjmp(context, tree, c0, c1):
    op, yes_label, no_label = tree.value
    d = context.new_reg(HadesRegister)
    Bop = jump_opnames[op]
    context.emit(Bop(d, c0, c1))
    context.emit(Bnez(d, jumps=[yes_label]))
    context.emit(Jal(registers.ra, no_label.name, jumps=[no_label]))
    return