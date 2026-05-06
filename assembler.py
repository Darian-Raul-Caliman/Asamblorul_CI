import re


class Assembler:
    def __init__(self):
        self.opcodes_c1 = {'MOV': '0000', 'ADD': '0001', 'SUB': '0010'}
        self.opcodes_c2 = {'CLR': '1000000000', 'INC': '1000000010', 'DEC': '1000000011'}
        self.opcodes_c3 = {'BEQ': '11000010', 'BNE': '11000001', 'BR': '11000000'}
        self.opcodes_c4 = {'HALT': '1110000000001101'}
        self.labels = {}

    def parse_operand(self, operand):
        operand = operand.strip()
        if re.match(r'^\(R(\d+)\)$', operand, re.IGNORECASE):
            return '10', format(int(re.match(r'^\(R(\d+)\)$', operand).group(1)), '04b'), None
        if re.match(r'^R(\d+)$', operand, re.IGNORECASE):
            return '01', format(int(re.match(r'^R(\d+)$', operand).group(1)), '04b'), None
        if re.match(r'^([+\-]?\w+)$', operand):
            val = int(operand, 16) if operand.lower().startswith('0x') else int(operand, 10)
            return '00', '0000', val
        raise ValueError(f"Mod de adresare necunoscut: {operand}")

    def format_16bit_hex(self, val):
        if val < 0: val = (1 << 16) + val
        return f"{val & 0xFFFF:04X}"

    def format_8bit_binary(self, val):
        if val < 0: val = (1 << 8) + val
        return f"{val & 0xFF:08b}"

    def assemble_program(self, program_text):
        self.labels = {}
        lines = [line.split(';')[0].strip() for line in program_text.strip().split('\n')]
        pc = 0
        cleaned_lines = []

        # Trecerea 1: Calcul adrese și etichete
        for line in lines:
            if not line: continue
            if line.endswith(':'):
                self.labels[line[:-1]] = pc
                continue
            cleaned_lines.append((pc, line))
            parts = line.replace(',', ' ').split()
            words_count = 1
            if parts[0].upper() in self.opcodes_c1:
                if len(parts) > 2 and self.parse_operand(parts[2])[2] is not None: words_count += 1
                if len(parts) > 1 and self.parse_operand(parts[1])[2] is not None: words_count += 1
            elif parts[0].upper() in self.opcodes_c2:
                if len(parts) > 1 and self.parse_operand(parts[1])[2] is not None: words_count += 1
            pc += words_count * 2

        # Trecerea 2: Generare cod mașină
        machine_code_output = []
        for instruction_pc, line in cleaned_lines:
            parts = line.replace(',', ' ').split()
            mnemonic = parts[0].upper()
            try:
                if mnemonic in self.opcodes_c1:
                    mas, rs, ex_s = self.parse_operand(parts[2])
                    mad, rd, ex_d = self.parse_operand(parts[1])
                    base = f"{self.opcodes_c1[mnemonic]}{mas}{rs}{mad}{rd}"
                    words = [f"{int(base, 2):04X}"]
                    if ex_s is not None: words.append(self.format_16bit_hex(ex_s))
                    if ex_d is not None: words.append(self.format_16bit_hex(ex_d))
                    machine_code_output.append((instruction_pc, " ".join(words), line))
                elif mnemonic in self.opcodes_c2:
                    mad, rd, ex_d = self.parse_operand(parts[1])
                    base = f"{self.opcodes_c2[mnemonic]}{mad}{rd}"
                    words = [f"{int(base, 2):04X}"]
                    if ex_d is not None: words.append(self.format_16bit_hex(ex_d))
                    machine_code_output.append((instruction_pc, " ".join(words), line))
                elif mnemonic in self.opcodes_c4:
                    machine_code_output.append((instruction_pc, f"{int(self.opcodes_c4[mnemonic], 2):04X}", line))
                elif mnemonic in self.opcodes_c3:
                    target = parts[1]
                    offset = (self.labels[target] - (instruction_pc + 2)) // 2
                    base = f"{self.opcodes_c3[mnemonic]}{self.format_8bit_binary(offset)}"
                    machine_code_output.append((instruction_pc, f"{int(base, 2):04X}", line))
            except Exception as e:
                machine_code_output.append((instruction_pc, "EROARE", f"{line} -> {str(e)}"))

        return machine_code_output, self.labels