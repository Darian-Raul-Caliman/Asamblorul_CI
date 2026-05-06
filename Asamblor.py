import re
import tkinter as tk
from tkinter import ttk, messagebox


# --- 1. MOTORUL DE ASAMBLARE ---
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

        # Trecerea 1
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

        # Trecerea 2
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


# --- 2. EMULATORUL (Mașina Virtuală) ---
class Emulator:
    def __init__(self):
        self.registers = {f"R{i}": 0 for i in range(16)}
        self.pc = 0
        self.flags = {'Z': 0, 'N': 0, 'C': 0, 'V': 0}
        self.memory_instructions = {}  # Mapează PC -> Linie de cod (pentru simulare ușoară)
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
        """Extrage valoarea (fie din registru, fie valoare imediată)"""
        if operand.startswith('R'): return self.registers[operand]
        return int(operand, 16) if operand.lower().startswith('0x') else int(operand, 10)

    def set_flags(self, result):
        """Setează flag-ul Zero dacă rezultatul e 0"""
        self.flags['Z'] = 1 if result == 0 else 0

    def step(self):
        """Execută o singură instrucțiune"""
        if self.halted or self.pc not in self.memory_instructions:
            return False

        line = self.memory_instructions[self.pc]
        parts = line.replace(',', ' ').split()
        mnemonic = parts[0].upper()

        next_pc = self.pc + 2  # Presupunem 1 cuvânt. Ajustăm dacă e cazul.

        # Calculăm mărimea instrucțiunii pentru a ști cât avansăm PC-ul
        # Aceasta e o simulare simplificată a decodificării
        if mnemonic in ['MOV', 'ADD', 'SUB']:
            if not parts[2].startswith('R'): next_pc += 2  # Imediat la sursă
            if not parts[1].startswith('R'): next_pc += 2  # Imediat la dest
        elif mnemonic in ['CLR', 'INC', 'DEC']:
            if not parts[1].startswith('R'): next_pc += 2

        # Execuția logică
        if mnemonic == 'MOV':
            val = self.get_value(parts[2])
            self.registers[parts[1]] = val
        elif mnemonic == 'ADD':
            val = self.get_value(parts[2])
            res = (self.registers[parts[1]] + val) & 0xFFFF  # Menținem pe 16 biți
            self.registers[parts[1]] = res
            self.set_flags(res)
        elif mnemonic == 'SUB':
            val = self.get_value(parts[2])
            res = (self.registers[parts[1]] - val) & 0xFFFF
            self.registers[parts[1]] = res
            self.set_flags(res)
        elif mnemonic == 'CLR':
            self.registers[parts[1]] = 0
            self.set_flags(0)
        elif mnemonic == 'INC':
            res = (self.registers[parts[1]] + 1) & 0xFFFF
            self.registers[parts[1]] = res
            self.set_flags(res)
        elif mnemonic == 'DEC':
            res = (self.registers[parts[1]] - 1) & 0xFFFF
            self.registers[parts[1]] = res
            self.set_flags(res)
        elif mnemonic == 'BEQ':
            if self.flags['Z'] == 1:
                next_pc = self.labels[parts[1]]
        elif mnemonic == 'HALT':
            self.halted = True

        self.pc = next_pc
        return True


# --- 3. INTERFAȚA GRAFICĂ (IDE) ---
class AssemblerIDE:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulator CISC Complet")
        self.root.geometry("1100x600")

        self.assembler = Assembler()
        self.emulator = Emulator()
        self.pc_to_item = {}  # Mapează PC-ul la rândul din tabel pentru highlight

        # Layout principal 3 Coloane
        self.main_frame = tk.Frame(root, padx=10, pady=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. Stânga: Editor
        self.left_frame = tk.Frame(self.main_frame, width=300)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        tk.Label(self.left_frame, text="Cod Sursă:", font=("Arial", 11, "bold")).pack(anchor=tk.W)
        self.text_editor = tk.Text(self.left_frame, font=("Courier New", 12), width=35)
        self.text_editor.pack(fill=tk.BOTH, expand=True, pady=5)

        test_code = """CLR R1
MOV R2, 3
ET1:
INC R1
DEC R2
BEQ ET1
HALT"""
        self.text_editor.insert(tk.END, test_code)

        # Butoane Control
        btn_frame = tk.Frame(self.left_frame)
        btn_frame.pack(fill=tk.X)
        tk.Button(btn_frame, text="⚙️ Asamblează", bg="#4CAF50", fg="white", font=("Arial", 10, "bold"),
                  command=self.run_assembler).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        self.btn_step = tk.Button(btn_frame, text="⏭️ Step", bg="#2196F3", fg="white", font=("Arial", 10, "bold"),
                                  command=self.step_execution, state=tk.DISABLED)
        self.btn_step.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        self.btn_reset = tk.Button(btn_frame, text="🔄 Reset", bg="#f44336", fg="white", font=("Arial", 10, "bold"),
                                   command=self.reset_execution, state=tk.DISABLED)
        self.btn_reset.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        # 2. Centru: Cod Mașină
        self.mid_frame = tk.Frame(self.main_frame)
        self.mid_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        tk.Label(self.mid_frame, text="Memorie / Cod Mașină:", font=("Arial", 11, "bold")).pack(anchor=tk.W)

        self.tree = ttk.Treeview(self.mid_frame, columns=("PC", "HexCode", "Instruction"), show="headings", height=15)
        self.tree.heading("PC", text="PC")
        self.tree.heading("HexCode", text="Hex")
        self.tree.heading("Instruction", text="Instrucțiune")
        self.tree.column("PC", width=50, anchor=tk.CENTER)
        self.tree.column("HexCode", width=120, anchor=tk.CENTER)
        self.tree.column("Instruction", width=150, anchor=tk.W)
        self.tree.pack(fill=tk.BOTH, expand=True, pady=5)

        # Configurare highlight pentru linia curentă
        self.tree.tag_configure('current_pc', background='#FFF59D')  # Galben deschis

        # 3. Dreapta: Regiștri
        self.right_frame = tk.Frame(self.main_frame, width=200)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Label(self.right_frame, text="Regiștri (Live):", font=("Arial", 11, "bold")).pack(anchor=tk.W)

        self.reg_tree = ttk.Treeview(self.right_frame, columns=("Reg", "Val"), show="headings", height=17)
        self.reg_tree.heading("Reg", text="Reg")
        self.reg_tree.heading("Val", text="Valoare (Hex)")
        self.reg_tree.column("Reg", width=50, anchor=tk.CENTER)
        self.reg_tree.column("Val", width=100, anchor=tk.CENTER)
        self.reg_tree.pack(fill=tk.BOTH, expand=True, pady=5)

        self.update_registers_ui()

    def update_registers_ui(self):
        """Actualizează tabelul de regiștri vizual"""
        for item in self.reg_tree.get_children():
            self.reg_tree.delete(item)
        for i in range(16):
            reg_name = f"R{i}"
            val = self.emulator.registers[reg_name]
            self.reg_tree.insert("", tk.END, values=(reg_name, f"0x{val:04X}"))

        # Afișăm și Flag-urile jos
        flags_str = f"Z:{self.emulator.flags['Z']}  N:{self.emulator.flags['N']}  C:{self.emulator.flags['C']}"
        if hasattr(self, 'flags_label'):
            self.flags_label.config(text=flags_str)
        else:
            self.flags_label = tk.Label(self.right_frame, text=flags_str, font=("Courier", 11, "bold"), fg="blue")
            self.flags_label.pack(pady=5)

    def highlight_current_instruction(self):
        """Evidențiază rândul din tabel care corespunde cu PC-ul curent"""
        # Curățăm highlight-ul anterior
        for item in self.tree.get_children():
            self.tree.item(item, tags=())

        # Setăm noul highlight
        if self.emulator.pc in self.pc_to_item:
            item = self.pc_to_item[self.emulator.pc]
            self.tree.item(item, tags=('current_pc',))
            self.tree.see(item)  # Face scroll automat dacă e nevoie

    def run_assembler(self):
        source_code = self.text_editor.get("1.0", tk.END)
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.pc_to_item.clear()

        try:
            compiled_data, labels = self.assembler.assemble_program(source_code)

            # Populăm tabelul central
            for pc, machine_code, instruction in compiled_data:
                item = self.tree.insert("", tk.END, values=(f"{pc:04X}", machine_code, instruction))
                self.pc_to_item[pc] = item  # Salvăm referința pentru highlight

            # Încărcăm programul în Emulator
            self.emulator.load_program(compiled_data, labels)
            self.update_registers_ui()
            self.highlight_current_instruction()

            # Activăm butoanele
            self.btn_step.config(state=tk.NORMAL)
            self.btn_reset.config(state=tk.NORMAL)
            messagebox.showinfo("Succes", "Cod asamblat și încărcat în memorie!")

        except Exception as e:
            messagebox.showerror("Eroare", str(e))

    def step_execution(self):
        """Execută un pas în simulator"""
        if self.emulator.halted:
            messagebox.showinfo("Oprit", "Execuția a ajuns la instrucțiunea HALT.")
            return

        success = self.emulator.step()
        if success:
            self.update_registers_ui()
            self.highlight_current_instruction()
            if self.emulator.halted:
                self.btn_step.config(state=tk.DISABLED)
        else:
            messagebox.showwarning("Atenție", "S-a atins sfârșitul memoriei sau o instrucțiune necunoscută.")

    def reset_execution(self):
        self.emulator.reset()
        self.update_registers_ui()
        self.highlight_current_instruction()
        self.btn_step.config(state=tk.NORMAL)


if __name__ == "__main__":
    root = tk.Tk()
    app = AssemblerIDE(root)
    root.mainloop()