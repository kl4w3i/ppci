from ..registers import Register, RegisterClass
from ... import ir

class HadesRegister(Register):
    bitsize = 32
    @classmethod
    def from_num(cls, num):
        return num_reg_map[num]

r0 = HadesRegister('r0', 0)
r1 = HadesRegister('r1', 1)
r2 = HadesRegister('r2', 2)
r3 = HadesRegister('r3', 3)
r4 = HadesRegister('r4', 4)
r5 = HadesRegister('r5', num=5, aka=('ra', ))
r6 = HadesRegister('r6', num=6, aka=('fp', ))
r7 = HadesRegister('r7', num=7, aka=('sp', ))

ra = r5
fp = r6
sp = r7

HadesRegister.registers = [ r0, r1, r2, r3, r4, r5, r6, r7 ]
num_reg_map = {r.num: r for r in HadesRegister.registers}
all_registers =  [ r1, r2, r3, r4, r5 ]

register_classes = [
    RegisterClass(
        "reg",
        [ir.i16, ir.i8, ir.u16, ir.u8, ir.i32, ir.u32, ir.ptr],
        HadesRegister,
        all_registers
    )
]

caller_save = []
callee_save = []