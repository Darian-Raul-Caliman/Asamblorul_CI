# Assembler and Simulator for CISC Processor (16-bit)

This project represents a complete didactic development environment (IDE) that includes a **Assembler (Two-Pass Assembler)** and an **Emulator (Virtual Machine)** with graphical visualization of the data flow (Datapath), developed in Python.

The project is based on the architecture of a CISC microprogrammed processor, with dedicated buses: SBUS, DBUS and RBUS.

## 🛠️ Project Structure (MVC)

The project has been modularized for better maintainability and clarity of the code:
* `assembler.py` - Contains the parsing and assembly engine. It transforms the mnemonic code into machine code (Hex/Binary), resolves labels (Two-Pass) and calculates offsets for jumps.
* `emulator.py` - Represents the virtual machine. Manages instruction memory, register file (R0 - R15), Program Counter (PC) and flags (Z, N, C, V).
* `main.py` - Graphical user interface (GUI) made with `tkinter`. Includes text editor, memory view, live register table and Canvas animation for Datapath.

## ⚙️ Implemented Architectural Specifications

The simulated processor supports 4 main instruction classes:
1. **Class 1 (2 operands):** `MOV`, `ADD`, `SUB`, `CMP`, `AND`, `OR`, `XOR`. Format: `OPCODE (4b) | MAS (2b) | RS (4b) | MAD (2b) | RD (4b)`.
2. **Class 2 (1 operand):** `CLR`, `NEG`, `INC`, `DEC`, etc. Format: `OPCODE (10b) | MAD (2b) | RD (4b)`.
3. **Class 3 (Relative Jumps):** `BR`, `BNE`, `BEQ`, etc. Format: `OPCODE (8b) | OFFSET (8b)`.
4. **Class 4 (Miscellaneous):** `HALT`, `CLC`, `SEC`, `NOP`, etc. Format: `OPCODE (16b)`.

**Supported addressing modes:**
* `00` - Immediate (ex: `124`)
* `01` - Direct Register (ex: `R1`)
* `10` - Indirect Register (ex: `(R1)`)
* `11` - Indexed (ex: `124(R5)`)

*Note: Instructions with immediate or indexed addressing will generate additional words in the virtual machine memory.*

## 🚀 How to run

### Prerequisites:
* Python 3.x installed on the system.
* No external libraries required (uses strictly the standard `re` and `tkinter` modules).

### Run:
Open a terminal or command line in the project folder and run:
```bash
python main.py

<img width="1497" height="1326" alt="image" src="https://github.com/user-attachments/assets/9226d7ab-7f0e-4b48-8a2a-9f45ddd8280d" />
