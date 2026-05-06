import tkinter as tk
from tkinter import ttk, messagebox

# --- AICI IMPORTĂM CLASELE DIN CELELALTE FIȘIERE ---
from assembler import Assembler
from emulator import Emulator


class AssemblerIDE:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulator CISC cu Animație Datapath")
        self.root.geometry("1000x850")

        # Instanțiem modulele externe
        self.assembler = Assembler()
        self.emulator = Emulator()

        self.pc_to_item = {}

        # --- Interfața UI (Layout-ul rămâne același ca în codul precedent) ---
        self.top_frame = tk.Frame(root, padx=10, pady=5)
        self.top_frame.pack(fill=tk.BOTH, expand=True)

        self.bot_frame = tk.Frame(root, padx=10, pady=5, bg="white", relief=tk.SUNKEN, borderwidth=2)
        self.bot_frame.pack(fill=tk.BOTH, expand=False, side=tk.BOTTOM)

        # Stânga: Editor
        self.left_frame = tk.Frame(self.top_frame, width=300)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        tk.Label(self.left_frame, text="Cod Sursă:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        self.text_editor = tk.Text(self.left_frame, font=("Courier New", 12), width=30, height=12)
        self.text_editor.pack(fill=tk.BOTH, expand=True)

        test_code = """CLR R1
MOV R2, 3
BUCLA:
ADD R1, R2
DEC R2
BNE BUCLA
HALT"""
        self.text_editor.insert(tk.END, test_code)

        btn_frame = tk.Frame(self.left_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        tk.Button(btn_frame, text="⚙️ Asamblează", bg="#4CAF50", fg="white", command=self.run_assembler).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        self.btn_step = tk.Button(btn_frame, text="⏭️ Step", bg="#2196F3", fg="white", command=self.step_execution,
                                  state=tk.DISABLED)
        self.btn_step.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        self.btn_reset = tk.Button(btn_frame, text="🔄 Reset", bg="#f44336", fg="white", command=self.reset_execution,
                                   state=tk.DISABLED)
        self.btn_reset.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        # Centru: Cod Mașină
        self.mid_frame = tk.Frame(self.top_frame)
        self.mid_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        tk.Label(self.mid_frame, text="Cod Mașină:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        self.tree = ttk.Treeview(self.mid_frame, columns=("PC", "HexCode", "Instruction"), show="headings", height=12)
        self.tree.heading("PC", text="PC");
        self.tree.column("PC", width=50, anchor=tk.CENTER)
        self.tree.heading("HexCode", text="Hex");
        self.tree.column("HexCode", width=120, anchor=tk.CENTER)
        self.tree.heading("Instruction", text="Instrucțiune");
        self.tree.column("Instruction", width=150, anchor=tk.W)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.tag_configure('current_pc', background='#FFF59D')

        # Dreapta: Regiștri
        self.right_frame = tk.Frame(self.top_frame, width=150)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y)
        tk.Label(self.right_frame, text="Regiștri:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        self.reg_tree = ttk.Treeview(self.right_frame, columns=("Reg", "Val"), show="headings", height=12)
        self.reg_tree.heading("Reg", text="Reg");
        self.reg_tree.column("Reg", width=50, anchor=tk.CENTER)
        self.reg_tree.heading("Val", text="Valoare");
        self.reg_tree.column("Val", width=80, anchor=tk.CENTER)
        self.reg_tree.pack(fill=tk.BOTH, expand=True)

        self.flags_label = tk.Label(self.right_frame, text="Z:0  N:0  C:0", font=("Courier", 11, "bold"), fg="blue")
        self.flags_label.pack(pady=5)
        self.update_registers_ui()

        # Jos: Animația Canvas
        tk.Label(self.bot_frame, text="Vizualizare Hardware Live (Datapath)", font=("Arial", 11, "bold"),
                 bg="white").pack(anchor=tk.NW)
        self.canvas = tk.Canvas(self.bot_frame, height=220, bg="white", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.draw_architecture()

    def draw_architecture(self):
        # Bloc Registre
        self.canvas.create_rectangle(50, 20, 150, 180, fill="#E0E0E0", width=2)
        self.canvas.create_text(100, 100, text="REGISTER\nFILE\n(R0 - R15)", justify=tk.CENTER,
                                font=("Arial", 10, "bold"))

        # ALU
        self.canvas.create_polygon(700, 40, 800, 70, 800, 130, 700, 160, 730, 100, fill="#FFF9C4", outline="#FBC02D",
                                   width=2)
        self.canvas.create_text(760, 100, text="ALU", font=("Arial", 12, "bold"))

        # SBUS
        self.canvas.create_line(150, 60, 700, 60, arrow=tk.LAST, width=3, fill="#2196F3")
        self.canvas.create_text(425, 45, text="SBUS (Sursa)", fill="#2196F3", font=("Arial", 10, "bold"))

        # DBUS
        self.canvas.create_line(150, 140, 700, 140, arrow=tk.LAST, width=3, fill="#4CAF50")
        self.canvas.create_text(425, 125, text="DBUS (Destinația)", fill="#4CAF50", font=("Arial", 10, "bold"))

        # RBUS
        self.canvas.create_line(800, 100, 850, 100, 850, 200, 100, 200, 100, 180, arrow=tk.LAST, width=3,
                                fill="#F44336")
        self.canvas.create_text(425, 185, text="RBUS (Rezultat)", fill="#F44336", font=("Arial", 10, "bold"))

    def animate_data(self, x1, y1, x2, y2, color, text_val, step_cb=None):
        r = 15
        circle = self.canvas.create_oval(x1 - r, y1 - r, x1 + r, y1 + r, fill=color, outline="black")
        txt = self.canvas.create_text(x1, y1, text=f"{text_val:04X}", font=("Courier", 8, "bold"))

        steps = 20
        dx = (x2 - x1) / steps
        dy = (y2 - y1) / steps

        def move(step_count):
            if step_count < steps:
                self.canvas.move(circle, dx, dy)
                self.canvas.move(txt, dx, dy)
                self.root.after(30, move, step_count + 1)
            else:
                self.canvas.delete(circle)
                self.canvas.delete(txt)
                if step_cb: step_cb()

        move(0)

    def trigger_animation(self, anim_data):
        self.btn_step.config(state=tk.DISABLED)
        op = anim_data['op']

        def phase_3_write():
            if anim_data['res'] is not None:
                op_text = self.canvas.create_text(760, 120, text=f"Op:{op}", fill="red", font=("Arial", 8, "bold"))
                self.root.after(400, lambda: self.canvas.delete(op_text))

                def finish_anim():
                    self.update_registers_ui()
                    self.highlight_current_instruction()
                    self.btn_step.config(state=tk.NORMAL)

                self.animate_data(800, 100, 100, 200, "#FFCDD2", anim_data['res'], finish_anim)
            else:
                self.update_registers_ui()
                self.highlight_current_instruction()
                self.btn_step.config(state=tk.NORMAL)

        if anim_data['src'] is not None and anim_data['dest'] is not None:
            self.animate_data(150, 60, 700, 60, "#BBDEFB", anim_data['src'])
            self.animate_data(150, 140, 700, 140, "#C8E6C9", anim_data['dest'], phase_3_write)
        elif anim_data['src'] is not None:
            self.animate_data(150, 60, 700, 60, "#BBDEFB", anim_data['src'], phase_3_write)
        elif anim_data['dest'] is not None:
            self.animate_data(150, 140, 700, 140, "#C8E6C9", anim_data['dest'], phase_3_write)
        else:
            phase_3_write()

    def update_registers_ui(self):
        for item in self.reg_tree.get_children(): self.reg_tree.delete(item)
        for i in range(16):
            self.reg_tree.insert("", tk.END, values=(f"R{i}", f"0x{self.emulator.registers[f'R{i}']:04X}"))
        self.flags_label.config(
            text=f"Z:{self.emulator.flags['Z']}  N:{self.emulator.flags['N']}  C:{self.emulator.flags['C']}")

    def highlight_current_instruction(self):
        for item in self.tree.get_children(): self.tree.item(item, tags=())
        if self.emulator.pc in self.pc_to_item:
            item = self.pc_to_item[self.emulator.pc]
            self.tree.item(item, tags=('current_pc',))
            self.tree.see(item)

    def run_assembler(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        self.pc_to_item.clear()
        try:
            compiled_data, labels = self.assembler.assemble_program(self.text_editor.get("1.0", tk.END))
            for pc, machine_code, instruction in compiled_data:
                self.pc_to_item[pc] = self.tree.insert("", tk.END, values=(f"{pc:04X}", machine_code, instruction))
            self.emulator.load_program(compiled_data, labels)
            self.update_registers_ui()
            self.highlight_current_instruction()
            self.btn_step.config(state=tk.NORMAL)
            self.btn_reset.config(state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror("Eroare", str(e))

    def step_execution(self):
        if self.emulator.halted:
            messagebox.showinfo("Oprit", "Execuția a ajuns la instrucțiunea HALT.")
            return
        success, anim_data = self.emulator.step()
        if success:
            if anim_data and anim_data['op'] not in ['BEQ', 'BNE', 'BR', 'HALT']:
                self.trigger_animation(anim_data)
            else:
                self.update_registers_ui()
                self.highlight_current_instruction()
                if self.emulator.halted: self.btn_step.config(state=tk.DISABLED)

    def reset_execution(self):
        self.emulator.reset()
        self.update_registers_ui()
        self.highlight_current_instruction()
        self.btn_step.config(state=tk.NORMAL)


if __name__ == "__main__":
    root = tk.Tk()
    app = AssemblerIDE(root)
    root.mainloop()