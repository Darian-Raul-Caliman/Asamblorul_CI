class Emulator:
    def __init__(self):
        self.registers = {f"R{i}": 0 for i in range(16)}
        self.pc = 0
        self.flags = {'Z': 0, 'N': 0, 'C': 0, 'V': 0}
        self.memory_instructions = {}
        self.labels = {}
        self.halted = False

    def reset(self):
        self.registers = {f"R{i}": 0 for i in range(16)}
        self.pc = 0
        self.flags = {'Z': 0, 'N': 0, 'C': 0, 'V': 0}
        self.halted = False

    def load_program(self, compiled_data, labels):
        self.reset()
        self.labels = labels
        self.memory_instructions = {pc: line for pc, hex_code, line in compiled_data}

    def get_value(self, operand):
        if operand.startswith('R'): return self.registers[operand]
        return int(operand, 16) if operand.lower().startswith('0x') else int(operand, 10)

    def set_flags(self, result):
        self.flags['Z'] = 1 if result == 0 else 0

    def step(self):
        if self.halted or self.pc not in self.memory_instructions:
            return False, None

        line = self.memory_instructions[self.pc]
        parts = line.replace(',', ' ').split()
        mnemonic = parts[0].upper()
        next_pc = self.pc + 2

        if mnemonic in ['MOV', 'ADD', 'SUB']:
            if not parts[2].startswith('R'): next_pc += 2
            if not parts[1].startswith('R'): next_pc += 2
        elif mnemonic in ['CLR', 'INC', 'DEC']:
            if not parts[1].startswith('R'): next_pc += 2

        anim_data = {"op": mnemonic, "src": None, "dest": None, "res": None, "reg": None}

        if mnemonic == 'MOV':
            val = self.get_value(parts[2])
            self.registers[parts[1]] = val
            anim_data.update({"src": val, "res": val, "reg": parts[1]})
        elif mnemonic == 'ADD':
            val = self.get_value(parts[2])
            res = (self.registers[parts[1]] + val) & 0xFFFF
            anim_data.update({"src": val, "dest": self.registers[parts[1]], "res": res, "reg": parts[1]})
            self.registers[parts[1]] = res
            self.set_flags(res)
        elif mnemonic == 'SUB':
            val = self.get_value(parts[2])
            res = (self.registers[parts[1]] - val) & 0xFFFF
            anim_data.update({"src": val, "dest": self.registers[parts[1]], "res": res, "reg": parts[1]})
            self.registers[parts[1]] = res
            self.set_flags(res)
        elif mnemonic == 'CLR':
            self.registers[parts[1]] = 0
            anim_data.update({"res": 0, "reg": parts[1]})
            self.set_flags(0)
        elif mnemonic in ['INC', 'DEC']:
            val = 1 if mnemonic == 'INC' else -1
            res = (self.registers[parts[1]] + val) & 0xFFFF
            anim_data.update({"dest": self.registers[parts[1]], "res": res, "reg": parts[1]})
            self.registers[parts[1]] = res
            self.set_flags(res)
        elif mnemonic == 'BEQ':
            if self.flags['Z'] == 1:
                next_pc = self.labels[parts[1]]
        elif mnemonic == 'BNE':
            if self.flags['Z'] == 0:
                next_pc = self.labels[parts[1]]
        elif mnemonic == 'HALT':
            self.halted = True

        self.pc = next_pc
        return True, anim_data