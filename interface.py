import asyncio
import json
import logging
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog

from dobot import Robot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DobotInterface:
    def __init__(self):
        self.robot = None
        self.loop = None
        self.thread = None
        self.running = False
        self.saved_points = []

        self.root = tk.Tk()
        self.root.title("DobotDraw - Interface")
        self.root.geometry("520x700")
        self.root.minsize(520, 500)
        self.root.resizable(True, True)

        self._build_ui()

    def _build_ui(self):
        canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self._build_content()

        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

    def _build_content(self):
        style = ttk.Style()
        style.theme_use("clam")

        frame_status = ttk.LabelFrame(self.scrollable_frame, text="Conexao")
        frame_status.pack(fill="x", padx=10, pady=5)

        self.lbl_status = ttk.Label(frame_status, text="Desconectado", foreground="red")
        self.lbl_status.pack(side="left", padx=10, pady=5)

        self.btn_connect = ttk.Button(frame_status, text="Conectar", command=self._toggle_connection)
        self.btn_connect.pack(side="right", padx=10, pady=5)

        frame_manual = ttk.LabelFrame(self.scrollable_frame, text="Controle Manual")
        frame_manual.pack(fill="x", padx=10, pady=5)

        frame_step = ttk.Frame(frame_manual)
        frame_step.pack(fill="x", padx=5, pady=5)

        ttk.Label(frame_step, text="Passo (mm):").pack(side="left")
        self.entry_step = ttk.Entry(frame_step, width=8)
        self.entry_step.insert(0, "10")
        self.entry_step.pack(side="left", padx=5)

        ttk.Button(frame_step, text="Ler Pose", command=self._read_pose).pack(side="right", padx=5)

        frame_jog = ttk.Frame(frame_manual)
        frame_jog.pack(fill="x", padx=5, pady=5)

        ttk.Button(frame_jog, text="+X", command=lambda: self._jog("x", 1)).grid(row=0, column=1, padx=2, pady=2)
        ttk.Button(frame_jog, text="-X", command=lambda: self._jog("x", -1)).grid(row=0, column=3, padx=2, pady=2)
        ttk.Button(frame_jog, text="+Y", command=lambda: self._jog("y", 1)).grid(row=1, column=0, padx=2, pady=2)
        ttk.Button(frame_jog, text="-Y", command=lambda: self._jog("y", -1)).grid(row=1, column=4, padx=2, pady=2)
        ttk.Button(frame_jog, text="+Z", command=lambda: self._jog("z", 1)).grid(row=2, column=1, padx=2, pady=2)
        ttk.Button(frame_jog, text="-Z", command=lambda: self._jog("z", -1)).grid(row=2, column=3, padx=2, pady=2)
        ttk.Button(frame_jog, text="+R", command=lambda: self._jog("r", 1)).grid(row=3, column=1, padx=2, pady=2)
        ttk.Button(frame_jog, text="-R", command=lambda: self._jog("r", -1)).grid(row=3, column=3, padx=2, pady=2)

        frame_tools = ttk.Frame(frame_manual)
        frame_tools.pack(fill="x", padx=5, pady=5)

        ttk.Button(frame_tools, text="Abrir Garra", command=lambda: self._run(self.robot.tool.gripper(False))).pack(
            side="left", expand=True, fill="x", padx=2
        )
        ttk.Button(frame_tools, text="Fechar Garra", command=lambda: self._run(self.robot.tool.gripper(True))).pack(
            side="left", expand=True, fill="x", padx=2
        )
        ttk.Button(frame_tools, text="Sucao ON", command=lambda: self._run(self.robot.tool.suction(True))).pack(
            side="left", expand=True, fill="x", padx=2
        )
        ttk.Button(frame_tools, text="Sucao OFF", command=lambda: self._run(self.robot.tool.suction(False))).pack(
            side="left", expand=True, fill="x", padx=2
        )

        frame_save = ttk.Frame(frame_manual)
        frame_save.pack(fill="x", padx=5, pady=5)

        ttk.Button(frame_save, text="Salvar Coordenada", command=self._save_point).pack(
            side="left", expand=True, fill="x", padx=2
        )
        ttk.Button(frame_save, text="Exportar JSON", command=self._export_points).pack(
            side="left", expand=True, fill="x", padx=2
        )
        ttk.Button(frame_save, text="Limpar", command=self._clear_points).pack(
            side="left", expand=True, fill="x", padx=2
        )

        frame_list = ttk.Frame(frame_manual)
        frame_list.pack(fill="both", expand=True, padx=5, pady=5)

        self.list_points = tk.Listbox(frame_list, height=5)
        self.list_points.pack(side="left", fill="both", expand=True)

        scrollbar_points = ttk.Scrollbar(frame_list, orient="vertical", command=self.list_points.yview)
        scrollbar_points.pack(side="right", fill="y")
        self.list_points.config(yscrollcommand=scrollbar_points.set)

        self.lbl_pose = ttk.Label(frame_manual, text="Pose: --")
        self.lbl_pose.pack(padx=5, pady=2)

        frame_motion = ttk.LabelFrame(self.scrollable_frame, text="Movimento")
        frame_motion.pack(fill="x", padx=10, pady=5)

        ttk.Button(frame_motion, text="Home", command=lambda: self._run(self.robot.motion.home())).pack(
            side="left", expand=True, fill="x", padx=5, pady=5
        )
        ttk.Button(frame_motion, text="Parar Fila", command=lambda: self._run(self.robot.queue.stop())).pack(
            side="left", expand=True, fill="x", padx=5, pady=5
        )

        frame_canvas = ttk.LabelFrame(self.scrollable_frame, text="Desenho Continuo")
        frame_canvas.pack(fill="x", padx=10, pady=5)

        frame_cmd = ttk.Frame(frame_canvas)
        frame_cmd.pack(fill="x", padx=5, pady=5)

        ttk.Label(frame_cmd, text="X:").pack(side="left")
        self.entry_x = ttk.Entry(frame_cmd, width=8)
        self.entry_x.insert(0, "200")
        self.entry_x.pack(side="left", padx=2)

        ttk.Label(frame_cmd, text="Y:").pack(side="left")
        self.entry_y = ttk.Entry(frame_cmd, width=8)
        self.entry_y.insert(0, "0")
        self.entry_y.pack(side="left", padx=2)

        ttk.Label(frame_cmd, text="Z:").pack(side="left")
        self.entry_z = ttk.Entry(frame_cmd, width=8)
        self.entry_z.insert(0, "0")
        self.entry_z.pack(side="left", padx=2)

        ttk.Label(frame_cmd, text="R:").pack(side="left")
        self.entry_r = ttk.Entry(frame_cmd, width=8)
        self.entry_r.insert(0, "0")
        self.entry_r.pack(side="left", padx=2)

        frame_buttons = ttk.Frame(frame_canvas)
        frame_buttons.pack(fill="x", padx=5, pady=5)

        ttk.Button(frame_buttons, text="Iniciar CP", command=self._start_canvas).pack(
            side="left", expand=True, fill="x", padx=2
        )
        ttk.Button(frame_buttons, text="Linha", command=self._line).pack(
            side="left", expand=True, fill="x", padx=2
        )
        ttk.Button(frame_buttons, text="Parar CP", command=lambda: self._run(self.robot.canvas.stop())).pack(
            side="left", expand=True, fill="x", padx=2
        )

        frame_shapes = ttk.LabelFrame(self.scrollable_frame, text="Formas")
        frame_shapes.pack(fill="x", padx=10, pady=5)

        ttk.Button(frame_shapes, text="Quadrado 50mm", command=self._square).pack(
            fill="x", padx=10, pady=3
        )
        ttk.Button(frame_shapes, text="Circulo 30mm", command=self._circle).pack(
            fill="x", padx=10, pady=3
        )

        frame_io = ttk.LabelFrame(self.scrollable_frame, text="IO")
        frame_io.pack(fill="x", padx=10, pady=5)

        frame_io_buttons = ttk.Frame(frame_io)
        frame_io_buttons.pack(fill="x", padx=5, pady=5)

        ttk.Button(frame_io_buttons, text="Ligar Saida 0", command=lambda: self._run(self.robot.io.do(0, 1))).pack(
            side="left", expand=True, fill="x", padx=2
        )
        ttk.Button(frame_io_buttons, text="Desligar Saida 0", command=lambda: self._run(self.robot.io.do(0, 0))).pack(
            side="left", expand=True, fill="x", padx=2
        )

        frame_log = ttk.LabelFrame(self.scrollable_frame, text="Log")
        frame_log.pack(fill="both", expand=True, padx=10, pady=5)

        self.txt_log = scrolledtext.ScrolledText(frame_log, height=8, state="disabled")
        self.txt_log.pack(fill="both", expand=True, padx=5, pady=5)

    def _log(self, msg):
        self.txt_log.config(state="normal")
        self.txt_log.insert("end", msg + "\n")
        self.txt_log.see("end")
        self.txt_log.config(state="disabled")

    def _start_event_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.running = True
        self.loop.run_forever()

    def _run(self, coro):
        if self.loop is None or not self.running:
            messagebox.showwarning("Aviso", "Conecte o robô primeiro")
            return
        asyncio.run_coroutine_threadsafe(self._safe_run(coro), self.loop)

    async def _safe_run(self, coro):
        try:
            await coro
        except Exception as e:
            self._log(f"[ERRO] {e}")

    def _toggle_connection(self):
        if self.robot is None:
            threading.Thread(target=self._connect, daemon=True).start()
        else:
            threading.Thread(target=self._disconnect, daemon=True).start()

    def _connect(self):
        try:
            self._log("Conectando...")
            self.robot = Robot()
            fut = asyncio.run_coroutine_threadsafe(self.robot.connect(), self.loop)
            fut.result()
            self.lbl_status.config(text="Conectado", foreground="green")
            self.btn_connect.config(text="Desconectar")
            self._log("[OK] Conectado")
        except Exception as e:
            self._log(f"[ERRO] {e}")
            self.robot = None

    def _disconnect(self):
        try:
            fut = asyncio.run_coroutine_threadsafe(self.robot.disconnect(), self.loop)
            fut.result()
            self._log("[OK] Desconectado")
        except Exception as e:
            self._log(f"[ERRO] {e}")
        finally:
            self.robot = None
            self.lbl_status.config(text="Desconectado", foreground="red")
            self.btn_connect.config(text="Conectar")

    def _jog(self, axis, direction):
        try:
            step = float(self.entry_step.get())
        except ValueError:
            messagebox.showerror("Erro", "Passo deve ser numerico")
            return

        self._run(self.robot.motion.movj(
            x=step if axis == "x" else 0,
            y=step if axis == "y" else 0,
            z=step if axis == "z" else 0,
            r=step if axis == "r" else 0,
        ))

    def _read_pose(self):
        self._run(self._async_read_pose())

    async def _async_read_pose(self):
        try:
            pose = await self.robot.dashboard.get_pose()
            self.lbl_pose.config(text=f"Pose: {pose}")
            self._log(f"Pose: {pose}")
        except Exception as e:
            self._log(f"[ERRO] {e}")

    def _save_point(self):
        self._run(self._async_save_point())

    async def _async_save_point(self):
        try:
            pose = await self.robot.dashboard.get_pose()
            self.saved_points.append(pose)
            self.list_points.insert("end", str(pose))
            self._log(f"Salvo: {pose}")
        except Exception as e:
            self._log(f"[ERRO] {e}")

    def _export_points(self):
        if not self.saved_points:
            messagebox.showinfo("Info", "Nenhuma coordenada salva")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("Todos", "*.*")],
            title="Exportar coordenadas"
        )
        if file_path:
            try:
                with open(file_path, "w") as f:
                    json.dump(self.saved_points, f, indent=2)
                self._log(f"Exportado: {file_path}")
            except Exception as e:
                self._log(f"[ERRO] {e}")

    def _clear_points(self):
        self.saved_points.clear()
        self.list_points.delete(0, "end")
        self._log("Coordenadas limpas")

    def _start_canvas(self):
        self._run(self.robot.canvas.start(speed=100, acceleration=100))
        self._log("CP iniciado")

    def _line(self):
        try:
            x = float(self.entry_x.get())
            y = float(self.entry_y.get())
            z = float(self.entry_z.get())
            r = float(self.entry_r.get())
        except ValueError:
            messagebox.showerror("Erro", "X/Y/Z/R devem ser numeros")
            return
        self._run(self.robot.canvas.line(x, y, z, r))
        self._log(f"Linha para ({x}, {y}, {z}, r={r})")

    def _square(self):
        self._run(self.robot.drawer.draw_square(100, 100, 50, z=0))
        self._log("Desenhando quadrado 50mm")

    def _circle(self):
        self._run(self.robot.drawer.draw_circle(200, 200, 30, z=0))
        self._log("Desenhando circulo 30mm")

    def run(self):
        self.thread = threading.Thread(target=self._start_event_loop, daemon=True)
        self.thread.start()
        self.root.mainloop()


def main():
    app = DobotInterface()
    app.run()


if __name__ == "__main__":
    main()
