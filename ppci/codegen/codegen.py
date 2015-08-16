"""
    Target independent code generator part. The target is provided when
    the generator is created.
"""

from .. import ir
from ..irutils import Verifier, split_block
from ..target.target import Target
from ..target.target import RegisterUseDef
from ..target.isa import Register, Instruction
from .selectiongraph import SelectionGraph
from .irdag import SelectionGraphBuilder, FunctionInfo, prepare_function_info
from .instructionselector import InstructionSelector1
from .instructionscheduler import InstructionScheduler
from .registerallocator import RegisterAllocator
from ..binutils.outstream import MasterOutputStream, FunctionOutputStream
import logging


class CodeGenerator:
    """ Generic code generator. """
    def __init__(self, target):
        assert isinstance(target, Target), target
        self.logger = logging.getLogger('codegen')
        self.target = target
        self.sgraph_builder = SelectionGraphBuilder()
        self.instruction_selector = InstructionSelector1(target.isa)
        self.instruction_scheduler = InstructionScheduler()
        self.register_allocator = RegisterAllocator()
        self.verifier = Verifier()

    def emit_frame_to_stream(self, frame, outs):
        """
            Add code for the prologue and the epilogue. Add a label, the
            return instruction and the stack pointer adjustment for the frame.
            At this point we know how much stack space must be reserved for
            locals and what registers should be saved.
        """
        # Materialize the register allocated instructions into a stream of
        # real instructions.
        self.logger.debug('Emitting instructions')

        # Prefix code:
        for instruction in frame.prologue():
            outs.emit(instruction)

        for ins in frame.instructions:
            assert isinstance(ins, Instruction) and ins.is_colored, str(ins)
            outs.emit(ins)

        # Postfix code (this uses the emit function):
        for instruction in frame.epilogue():
            outs.emit(instruction)

    def select_and_schedule(self, ir_function, frame, reporter):
        self.logger.debug('Selecting instructions')

        # Create a object that carries global function info:
        function_info = FunctionInfo(frame)
        prepare_function_info(function_info, ir_function)

        tree_method = True
        if tree_method:
            self.instruction_selector.select(ir_function, frame, function_info, reporter)
        else:
            # Build a graph:
            self.sgraph_builder.build(ir_function, function_info)
            reporter.message('Selection graph')
            reporter.dump_sgraph(sgraph)

            # Schedule instructions:
            self.instruction_scheduler.schedule(sgraph, frame)

    def define_arguments_live(self, frame, arguments):
        frame.instructions.insert(0, RegisterUseDef())
        ins0 = frame.instructions[0]
        assert type(ins0) is RegisterUseDef
        for idx, _ in enumerate(arguments):
            arg_loc = frame.arg_loc(idx)
            if isinstance(arg_loc, Register):
                ins0.add_def(arg_loc)

    def generate_function(self, ir_function, outs, reporter):
        """ Generate code for one function into a frame """
        self.logger.info('Generating {} code for function {}'
                         .format(self.target, ir_function.name))

        reporter.function_header(ir_function, self.target)
        instruction_list = []
        outs = MasterOutputStream([
            FunctionOutputStream(instruction_list.append),
            outs])

        # Split too large basic blocks in smaller chunks (for literal pools):
        # TODO: fix arbitrary number of 500. This works for arm and thumb..
        for block in ir_function:
            max_block_len = 200
            while len(block) > max_block_len:
                self.logger.debug('{} too large, splitting up'.format(block))
                _, block = split_block(block, pos=max_block_len)

        # Create a frame for this function:
        frame = self.target.FrameClass(ir.label_name(ir_function))

        # Select instructions and schedule them:
        self.select_and_schedule(ir_function, frame, reporter)

        reporter.message('Selected instruction for {}'.format(ir_function))
        reporter.dump_frame(frame)

        # Define arguments live at first instruction:
        self.define_arguments_live(frame, ir_function.arguments)

        # Do register allocation:
        self.register_allocator.alloc_frame(frame)
        # TODO: Peep-hole here?

        # Add label and return and stack adjustment:
        self.emit_frame_to_stream(frame, outs)
        reporter.function_footer(instruction_list)

    def generate(self, ircode, outs, reporter):
        """ Generate code into output stream """
        assert isinstance(ircode, ir.Module)

        self.logger.info('Generating {} code for module {}'
                         .format(self.target, ircode.name))

        # Generate code for global variables:
        outs.select_section('data')
        for var in ircode.Variables:
            self.target.emit_global(outs, ir.label_name(var), var.amount)

        # Generate code for functions:
        # Munch program into a bunch of frames. One frame per function.
        # Each frame has a flat list of abstract instructions.
        outs.select_section('code')
        for function in ircode.Functions:
            self.generate_function(function, outs, reporter)
