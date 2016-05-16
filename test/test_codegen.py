#!/usr/bin/python

import unittest
import io
from ppci import ir
from ppci.irutils import Builder, Writer
from ppci.codegen.irdag import SelectionGraphBuilder, DagSplitter
from ppci.codegen.irdag import FunctionInfo, prepare_function_info
from ppci.arch.example import ExampleArch
from ppci.binutils.debuginfo import DebugDb
from ppci.api import get_arch


def print_module(m):
    f = io.StringIO()
    Writer().write(m, f)
    print(f.getvalue())


class IrDagTestCase(unittest.TestCase):
    """ Test if ir dag works good """
    def test_bug2(self):
        """ Check that if blocks are in function in strange order, the dag
        builder works """
        module = ir.Module('dut')
        function = ir.Procedure('tst')
        module.add_function(function)
        block1 = ir.Block('b1')
        block2 = ir.Block('b2')
        function.add_block(block1)
        function.add_block(block2)
        function.entry = block2
        con = ir.Const(2, 'con', ir.i32)
        block2.add_instruction(con)
        block2.add_instruction(ir.Jump(block1))
        block1.add_instruction(ir.Cast(con, 'con_cast', ir.i8))
        block1.add_instruction(ir.Terminator())

        # Target generation
        target = get_arch('arm')
        frame = target.new_frame('a', function)
        function_info = FunctionInfo(frame)
        debug_db = DebugDb()
        prepare_function_info(target, function_info, function)
        dag_builder = SelectionGraphBuilder(target, debug_db)
        sgraph = dag_builder.build(function, function_info)
        dag_splitter = DagSplitter(target, debug_db)

    def test_bug1(self):
        """
            This is the bug:

            function XXX sleep(i32 ms)
              entry:
                JUMP block12
              block12:
                i32 loaded = load global_tick
                i32 binop = loaded + ms
                JUMP block14
              block14:
                i32 loaded_2 = load global_tick
                IF binop > loaded_2 THEN block14 ELSE epilog
              epilog:
                Terminator

            Selection graph for function XXX sleep(i32 ms)

            entry:
                MOVI32[vreg0ms](REGI32[R1])
                JMP[bsp_sleep_block12:]
            block12:
                MOVI32[vreg1loaded](LDRI32(LABEL[bsp_global_tick]))
                JMP[bsp_sleep_block14:]
            block14:
                MOVI32[vreg4loaded_2](LDRI32(LABEL[bsp_global_tick]))
                CJMP[('>', bsp_sleep_block14:, bsp_sleep_epilog:)]
                    (REGI32[vreg5binop], REGI32[vreg4loaded_2])
            epilog:
        """
        builder = Builder()
        module = ir.Module('fuzz')
        global_tick = ir.Variable('global_tick', 4)
        module.add_variable(global_tick)
        builder.module = module
        function = builder.new_procedure('sleep')
        ms = ir.Parameter('ms', ir.i32)
        function.add_parameter(ms)
        builder.set_function(function)
        entry = builder.new_block()
        function.entry = entry
        builder.set_block(entry)
        block12 = builder.new_block()
        builder.emit(ir.Jump(block12))
        builder.set_block(block12)
        loaded = builder.emit(ir.Load(global_tick, 'loaded', ir.i32))
        binop = builder.emit(ir.Binop(loaded, '+', ms, 'binop', ir.i32))
        block14 = builder.new_block()
        builder.emit(ir.Jump(block14))
        builder.set_block(block14)
        loaded2 = builder.emit(ir.Load(global_tick, 'loaded2', ir.i32))
        epilog = builder.new_block()
        builder.emit(ir.CJump(binop, '>', loaded2, block14, epilog))
        builder.set_block(epilog)
        builder.emit(ir.Terminator())
        # print('module:')
        # print_module(module)

        # Target generation
        target = ExampleArch()
        frame = target.new_frame('a', function)
        function_info = FunctionInfo(frame)
        debug_db = DebugDb()
        prepare_function_info(target, function_info, function)
        dag_builder = SelectionGraphBuilder(target, debug_db)
        sgraph = dag_builder.build(function, function_info)
        dag_splitter = DagSplitter(target, debug_db)

        # print(function_info.value_map)
        for b in function:
            # root = function_info.block_roots[b]
            #print('root=', root)
            #for tree in dag_splitter.split_into_trees(root, frame):
            #    print('tree=', tree)
            pass
        # sg_value = function_info.value_map[binop]
        # print(function_info.value_map)
        # self.assertTrue(sg_value.vreg)


if __name__ == '__main__':
    unittest.main()
