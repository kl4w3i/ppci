from ... import ir
from ...binutils.assembler import BaseAssembler
from ..arch import Architecture
from ..arch_info import ArchInfo, TypeInfo, Endianness
from ..generic_instructions import Label, Alignment, RegisterUseDef
from ..data_instructions import data_isa
from ..runtime import get_runtime_files
from . import instructions, registers

class HadesArch(Architecture):
    name = "hades"

    def __init__(self, options=None):
        super().__init__(options=options)
        self.info = ArchInfo(
            type_infos={
                ir.i8: TypeInfo(1, 4),
                ir.u8: TypeInfo(1, 4),
                ir.i16: TypeInfo(2, 4),
                ir.u16: TypeInfo(2, 4),
                ir.i32: TypeInfo(4, 4),
                ir.u32: TypeInfo(4, 4),
                ir.i64: TypeInfo(8, 4),
                ir.u64: TypeInfo(8, 4),
                ir.f32: TypeInfo(4, 4),
                ir.f64: TypeInfo(8, 4),
                "int": ir.i32,
                "long": ir.i32,
                "ptr": ir.u32
            },
            register_classes = registers.register_classes,
            endianness=Endianness.LITTLE
        )
        self.isa = instructions.isa + data_isa
        self.assembler = BaseAssembler()
        self.assembler.gen_asm_parser(self.isa)

    def get_runtime(self):
        """ Retrieve the runtime for this target """
        from ...api import c3c

        c3_sources = get_runtime_files(["divsi3", "mulsi3"])
        obj = c3c(c3_sources, [], self)
        return obj

    def determine_arg_locations(self, arg_types):
        arg_locs = []
        int_regs = [registers.r1, registers.r2, registers.r3, registers.r4]
        for arg_type in arg_types:
            # Determine register:
            if arg_type in [
                ir.i8,
                ir.u8,
                ir.i16,
                ir.u16,
                ir.i32,
                ir.u32,
                ir.ptr,
            ]:
                reg = int_regs.pop(0)
            else:  # pragma: no cover
                raise NotImplementedError(str(arg_type))
            arg_locs.append(reg)
        return arg_locs
    
    def determine_rv_location(self, ret_type):
        """ return value in v0-v1 """
        if ret_type in [ir.i8, ir.u8, ir.i16, ir.u16, ir.i32, ir.u32, ir.ptr]:
            rv = registers.r1
        else:  # pragma: no cover
            raise NotImplementedError(str(ret_type))
        return rv

    def gen_prologue(self, frame):
        """ Returns prologue instruction sequence """

        yield Label(frame.name)

        yield instructions.Addi(registers.sp, registers.sp, -2)

        # First save return address (which is in a0):
        yield instructions.Store(registers.ra, registers.sp, 1)

        # Reserve stack space
        if frame.stacksize > 0:
            # Prepare frame pointer:
            yield self.move(registers.fp, registers.sp)
            size = -round_up(frame.stacksize)
            yield instructions.Addi(registers.sp, registers.sp, size // 4)

        # Callee save registers:
        for reg in self.get_callee_saved(frame):
            yield instructions.Push(reg)

    def gen_epilogue(self, frame):
        """ Return epilogue sequence """
        # Pop save registers back:
        for reg in reversed(self.get_callee_saved(frame)):
            yield instructions.Pop(reg)

        if frame.stacksize > 0:
            size = round_up(frame.stacksize)
            yield instructions.Addi(registers.sp, registers.sp, size // 4)

        yield instructions.Load(registers.fp, registers.sp, 0)

        # Restore return address:
        yield instructions.Load(registers.ra, registers.sp, 1)
        yield instructions.Addi(registers.sp, registers.sp, 2)

        # Return
        yield instructions.Jreg(registers.ra)
    
    def get_callee_saved(self, frame):
        saved_registers = []
        for reg in registers.callee_save:
            if frame.is_used(reg, self.info.alias):
                saved_registers.append(reg)
        return saved_registers

    def gen_call(self, frame, label, args, rv):
        arg_types = [a[0] for a in args]
        arg_locs = self.determine_arg_locations(arg_types)

        arg_regs = []
        for arg_loc, arg2 in zip(arg_locs, args):
            arg = arg2[1]
            if isinstance(arg_loc, registers.HadesRegister):
                arg_regs.append(arg_loc)
                yield self.move(arg_loc, arg)
            else:  # pragma: no cover
                raise NotImplementedError("Parameters in memory not impl")

        yield RegisterUseDef(uses=arg_regs)

        if isinstance(label, registers.HadesRegister):
            yield instructions.Jreg(label, clobbers=registers.caller_save)
        else:
            yield instructions.Jal(registers.ra, label, clobbers=registers.caller_save)

        if rv:
            retval_loc = self.determine_rv_location(rv[0])
            yield RegisterUseDef(defs=(retval_loc,))
            yield self.move(rv[1], retval_loc)
    
    def gen_function_enter(self, args):
        arg_types = [a[0] for a in args]
        arg_locs = self.determine_arg_locations(arg_types)

        arg_regs = set(
            l for l in arg_locs if isinstance(l, registers.HadesRegister)
        )
        yield RegisterUseDef(defs=arg_regs)

        for arg_loc, arg2 in zip(arg_locs, args):
            arg = arg2[1]
            if isinstance(arg_loc, registers.HadesRegister):
                yield self.move(arg, arg_loc)
            else:  # pragma: no cover
                raise NotImplementedError("Parameters in memory not impl")

    def gen_function_exit(self, rv):
        live_out = set()
        if rv:
            retval_loc = self.determine_rv_location(rv[0])
            yield self.move(retval_loc, rv[1])
            live_out.add(retval_loc)
        yield RegisterUseDef(uses=live_out)

    def move(self, dst, src):
        return instructions.mov(dst, src)

def round_up(s):
    return s + (4 - s % 4)