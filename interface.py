import asyncio
import json
import logging
import queue
import serial.tools.list_ports
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from dobot import Robot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable = ttk.Frame(canvas)

        self.scrollable.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.canvas = canvas
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))


class DobotInterface:
    def __init__(self):
        self.robot = None
        self.loop = None
        self.thread = None
        self.running = False
        self.saved_points = []
        self._ui_queue = queue.Queue()
        self._jog_active = False
        self._jog_axis = None
        self._jog_direction = 0
        self._jog_job = None

        self.root = tk.Tk()
        self.root.title("DobotDraw")
        self.root.geometry("700x850")
        self.root.minsize(600, 700)
        self.root.resizable(True, True)

        self._build_ui()

    def _build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabelFrame", padding=8)
        style.configure("TButton", padding=6)

        scroll_container = ScrollableFrame(self.root)
        scroll_container.pack(fill="both", expand=True, padx=10, pady=10)
        main = scroll_container.scrollable

        self._build_connection(main)
        self._build_operation_mode(main)
        self._build_manual_control(main)
        self._build_motion(main)
        self._build_canvas(main)
        self._build_shapes(main)
        self._build_io(main)
        self._build_log(main)
        self._update_operation_mode()

    def _build_connection(self, parent):
        frame = ttk.LabelFrame(parent, text="Conexao")
        frame.pack(fill="x", pady=5)

        top = ttk.Frame(frame)
        top.pack(fill="x", pady=5)

        self.lbl_status = ttk.Label(top, text="Desconectado", foreground="red", font=("Segoe UI", 10, "bold"))
        self.lbl_status.pack(side="left", padx=10)

        self.btn_connect = ttk.Button(top, text="Conectar", command=self._toggle_connection, width=12)
        self.btn_connect.pack(side="right", padx=10)

        mode_frame = ttk.Frame(frame)
        mode_frame.pack(fill="x", padx=10, pady=(0, 8))

        self.mode_var = tk.StringVar(value="usb")
        ttk.Radiobutton(mode_frame, text="USB direto (recomendado)", variable=self.mode_var, value="usb", command=self._toggle_mode).pack(side="left")
        ttk.Radiobutton(mode_frame, text="WebSocket (DobotLab)", variable=self.mode_var, value="websocket", command=self._toggle_mode).pack(side="left", padx=20)

        port_frame = ttk.Frame(frame)
        port_frame.pack(fill="x", padx=10, pady=(0, 8))

        ttk.Label(port_frame, text="Porta:").pack(side="left")
        self.port_var = tk.StringVar()
        self.combo_port = ttk.Combobox(port_frame, textvariable=self.port_var, width=14, state="disabled")
        self.combo_port["values"] = ["Auto"] + [p.device for p in serial.tools.list_ports.comports()]
        self.combo_port.set("Auto")
        self.combo_port.pack(side="left", padx=8)

    def _build_operation_mode(self, parent):
        frame = ttk.LabelFrame(parent, text="Operacao")
        frame.pack(fill="x", pady=5)

        self.operation_var = tk.StringVar(value="draw")

        ttk.Radiobutton(frame, text="Caneta (Desenho)", variable=self.operation_var, value="draw", command=self._update_operation_mode).pack(side="left", padx=10, pady=8)
        ttk.Radiobutton(frame, text="Garra", variable=self.operation_var, value="gripper", command=self._update_operation_mode).pack(side="left", padx=10, pady=8)
        ttk.Radiobutton(frame, text="Ventosa", variable=self.operation_var, value="suction", command=self._update_operation_mode).pack(side="left", padx=10, pady=8)

    def _build_manual_control(self, parent):
        frame = ttk.LabelFrame(parent, text="Controle Manual")
        frame.pack(fill="x", pady=5)

        top = ttk.Frame(frame)
        top.pack(fill="x", pady=5)

        ttk.Label(top, text="Passo (mm):").pack(side="left", padx=(10, 5))
        self.entry_step = ttk.Entry(top, width=8)
        self.entry_step.insert(0, "10")
        self.entry_step.pack(side="left", padx=5)

        ttk.Button(top, text="Ler Pose", command=self._read_pose).pack(side="right", padx=10)

        jog = ttk.Frame(frame)
        jog.pack(pady=5)

        btn_opts = {"width": 6, "padding": 4}

        def jog_bind(btn, axis, direction):
            btn.bind('<ButtonPress-1>', lambda e: self._start_jog(axis, direction))
            btn.bind('<ButtonRelease-1>', lambda e: self._stop_jog())

        b_xp = ttk.Button(jog, text="+X", **btn_opts)
        jog_bind(b_xp, "x", 1)
        b_xp.grid(row=0, column=1, padx=3, pady=3)

        b_xn = ttk.Button(jog, text="-X", **btn_opts)
        jog_bind(b_xn, "x", -1)
        b_xn.grid(row=0, column=3, padx=3, pady=3)

        b_yp = ttk.Button(jog, text="+Y", **btn_opts)
        jog_bind(b_yp, "y", 1)
        b_yp.grid(row=1, column=0, padx=3, pady=3)

        b_yn = ttk.Button(jog, text="-Y", **btn_opts)
        jog_bind(b_yn, "y", -1)
        b_yn.grid(row=1, column=4, padx=3, pady=3)

        b_zp = ttk.Button(jog, text="+Z", **btn_opts)
        jog_bind(b_zp, "z", 1)
        b_zp.grid(row=2, column=1, padx=3, pady=3)

        b_zn = ttk.Button(jog, text="-Z", **btn_opts)
        jog_bind(b_zn, "z", -1)
        b_zn.grid(row=2, column=3, padx=3, pady=3)

        b_rp = ttk.Button(jog, text="+R", **btn_opts)
        jog_bind(b_rp, "r", 1)
        b_rp.grid(row=3, column=1, padx=3, pady=3)

        b_rn = ttk.Button(jog, text="-R", **btn_opts)
        jog_bind(b_rn, "r", -1)
        b_rn.grid(row=3, column=3, padx=3, pady=3)

        tools = ttk.Frame(frame)
        tools.pack(fill="x", padx=10, pady=(0, 8))

        self.btn_abrir_garra = ttk.Button(tools, text="Abrir Garra", command=lambda: self._run(self.robot.tool.gripper(False)))
        self.btn_abrir_garra.pack(side="left", expand=True, fill="x", padx=2)

        self.btn_fechar_garra = ttk.Button(tools, text="Fechar Garra", command=lambda: self._run(self.robot.tool.gripper(True)))
        self.btn_fechar_garra.pack(side="left", expand=True, fill="x", padx=2)

        self.btn_sucao_on = ttk.Button(tools, text="Sucao ON", command=lambda: self._run(self.robot.tool.suction(True)))
        self.btn_sucao_on.pack(side="left", expand=True, fill="x", padx=2)

        self.btn_sucao_off = ttk.Button(tools, text="Sucao OFF", command=lambda: self._run(self.robot.tool.suction(False)))
        self.btn_sucao_off.pack(side="left", expand=True, fill="x", padx=2)

        save = ttk.Frame(frame)
        save.pack(fill="x", padx=10, pady=(0, 8))

        ttk.Button(save, text="Salvar Coordenada", command=self._save_point).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(save, text="Exportar JSON", command=self._export_points).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(save, text="Limpar", command=self._clear_points).pack(side="left", expand=True, fill="x", padx=2)

        pick_frame = ttk.Frame(frame)
        pick_frame.pack(fill="x", padx=10, pady=(0, 8))

        ttk.Button(pick_frame, text="Pegar e Entregar", command=self._pick_and_place).pack(
            side="left", expand=True, fill="x", padx=2
        )

        list_frame = ttk.Frame(frame)
        list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        self.list_points = tk.Listbox(list_frame, height=5)
        self.list_points.pack(side="left", fill="both", expand=True)

        scrollbar_points = ttk.Scrollbar(list_frame, orient="vertical", command=self.list_points.yview)
        scrollbar_points.pack(side="right", fill="y")
        self.list_points.config(yscrollcommand=scrollbar_points.set)

        self.lbl_pose = ttk.Label(frame, text="Pose: --")
        self.lbl_pose.pack(padx=10, pady=(0, 8))

    def _build_motion(self, parent):
        frame = ttk.LabelFrame(parent, text="Movimento")
        frame.pack(fill="x", pady=5)

        ttk.Button(frame, text="Home", command=lambda: self._run(self.robot.motion.home())).pack(
            side="left", expand=True, fill="x", padx=5, pady=5
        )
        ttk.Button(frame, text="Parar Fila", command=lambda: self._run(self.robot.queue.stop())).pack(
            side="left", expand=True, fill="x", padx=5, pady=5
        )

    def _build_canvas(self, parent):
        self.frame_canvas = ttk.LabelFrame(parent, text="Desenho Continuo")
        self.frame_canvas.pack(fill="x", pady=5)

        frame = self.frame_canvas
        frame_cmd = ttk.Frame(frame)
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

        frame_buttons = ttk.Frame(frame)
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

    def _build_shapes(self, parent):
        self.frame_shapes = ttk.LabelFrame(parent, text="Formas")
        self.frame_shapes.pack(fill="x", pady=5)

        ttk.Button(self.frame_shapes, text="Quadrado 50mm", command=self._square).pack(fill="x", padx=10, pady=4)
        ttk.Button(self.frame_shapes, text="Circulo 30mm", command=self._circle).pack(fill="x", padx=10, pady=(0, 8))

    def _build_io(self, parent):
        frame = ttk.LabelFrame(parent, text="IO")
        frame.pack(fill="x", pady=5)

        ttk.Button(frame, text="Ligar Saida 0", command=lambda: self._run(self.robot.io.do(0, 1))).pack(side="left", expand=True, fill="x", padx=10, pady=8)
        ttk.Button(frame, text="Desligar Saida 0", command=lambda: self._run(self.robot.io.do(0, 0))).pack(side="left", expand=True, fill="x", padx=10, pady=8)

    def _build_log(self, parent):
        frame = ttk.LabelFrame(parent, text="Log")
        frame.pack(fill="both", expand=True, pady=5)

        self.txt_log = tk.Text(frame, height=6, state="disabled", font=("Consolas", 8))
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
            self.root.after(0, lambda error=e: messagebox.showerror("Erro", f"{type(error).__name__}: {error}"))

    def _toggle_mode(self):
        mode = self.mode_var.get()
        if mode == "usb" or mode == "serial":
            self.combo_port.config(state="readonly")
            self._refresh_ports()
        else:
            self.combo_port.config(state="disabled")

    def _update_operation_mode(self):
        mode = self.operation_var.get()
        if mode == "draw":
            self._set_widgets_state(self.frame_canvas, "normal")
            self._set_widgets_state(self.frame_shapes, "normal")
            self._set_widgets_state(self.btn_abrir_garra, "disabled")
            self._set_widgets_state(self.btn_fechar_garra, "disabled")
            self._set_widgets_state(self.btn_sucao_on, "disabled")
            self._set_widgets_state(self.btn_sucao_off, "disabled")
        elif mode == "gripper":
            self._set_widgets_state(self.frame_canvas, "disabled")
            self._set_widgets_state(self.frame_shapes, "disabled")
            self._set_widgets_state(self.btn_abrir_garra, "normal")
            self._set_widgets_state(self.btn_fechar_garra, "normal")
            self._set_widgets_state(self.btn_sucao_on, "disabled")
            self._set_widgets_state(self.btn_sucao_off, "disabled")
        elif mode == "suction":
            self._set_widgets_state(self.frame_canvas, "disabled")
            self._set_widgets_state(self.frame_shapes, "disabled")
            self._set_widgets_state(self.btn_abrir_garra, "disabled")
            self._set_widgets_state(self.btn_fechar_garra, "disabled")
            self._set_widgets_state(self.btn_sucao_on, "normal")
            self._set_widgets_state(self.btn_sucao_off, "normal")

    def _set_widgets_state(self, widget, state):
        try:
            widget.config(state=state)
        except Exception:
            pass
        for child in widget.winfo_children():
            self._set_widgets_state(child, state)

    def _refresh_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        values = ["Auto"] + ports
        current = self.combo_port.get()
        self.combo_port["values"] = values
        if current and (current in values or current == "Auto"):
            self.combo_port.set(current)
        elif values:
            self.combo_port.set(values[0])

    def _toggle_connection(self):
        self._ui_queue.put(lambda msg=f"Botao conectar clicado. robot={self.robot}": self._log(msg))
        if self.robot is None:
            mode = self.mode_var.get()
            port = self.combo_port.get().strip()
            t = threading.Thread(target=self._connect, args=(mode, port), daemon=False)
            t.start()
        else:
            threading.Thread(target=self._disconnect, daemon=True).start()

    def _connect(self, mode, port):
        try:
            self._ui_queue.put(lambda msg=f"Tentando conectar: mode={mode}, port={port}": self._log(msg))
            if mode == "usb":
                if not port or port == "Auto":
                    self._ui_queue.put(lambda msg="Criando Robot(mode='usb', serial_port='auto')": self._log(msg))
                    self.robot = Robot(mode="usb", serial_port="auto")
                else:
                    self._ui_queue.put(lambda msg=f"Criando Robot(mode='usb', serial_port='{port}')": self._log(msg))
                    self.robot = Robot(mode="usb", serial_port=port)
            elif mode == "serial":
                if not port or port == "Auto":
                    self.robot = Robot(mode="serial", serial_port="auto")
                else:
                    self.robot = Robot(mode="serial", serial_port=port)
            else:
                self.robot = Robot(mode="websocket")

            self._ui_queue.put(lambda msg="Enviando comando connect()...": self._log(msg))
            fut = asyncio.run_coroutine_threadsafe(self.robot.connect(), self.loop)
            fut.result()
            self._ui_queue.put(lambda msg="Conexão estabelecida com sucesso": self._log(msg))
            self._ui_queue.put(self._on_connect_success)
        except Exception as e:
            self.robot = None
            import traceback
            tb = traceback.format_exc()
            self._ui_queue.put(lambda msg=f"FALHA NA CONEXÃO: {type(e).__name__}: {e}": self._log(msg))
            self._ui_queue.put(lambda msg=f"TRACEBACK: {tb}": self._log(msg))
            self._ui_queue.put(lambda error=e: self._on_connect_error(error))

    def _on_connect_success(self):
        self.lbl_status.config(text="Conectado", foreground="green")
        self.btn_connect.config(text="Desconectar")

    def _on_connect_error(self, error):
        self.lbl_status.config(text="Erro", foreground="red")
        messagebox.showerror("Erro de Conexao", f"Falha ao conectar:\n{type(error).__name__}: {error}")

    def _disconnect(self):
        self._ui_queue.put(lambda msg="Desconectando...": self._log(msg))
        try:
            fut = asyncio.run_coroutine_threadsafe(self.robot.disconnect(), self.loop)
            fut.result()
        except Exception:
            pass
        finally:
            self.robot = None
            self.lbl_status.config(text="Desconectado", foreground="red")
            self.btn_connect.config(text="Conectar")

    def _start_jog(self, axis, direction):
        if self.robot is None:
            return
        self._jog_active = True
        self._jog_axis = axis
        self._jog_direction = direction
        self._repeat_jog()

    def _stop_jog(self):
        self._jog_active = False
        self._jog_axis = None
        self._jog_direction = 0
        if self._jog_job is not None:
            self.root.after_cancel(self._jog_job)
            self._jog_job = None

    def _repeat_jog(self):
        if not self._jog_active or self._jog_axis is None:
            return
        try:
            step = float(self.entry_step.get())
        except ValueError:
            return
        axis = self._jog_axis
        direction = self._jog_direction
        self._run(self._async_jog(axis, direction, step))
        self._jog_job = self.root.after(120, self._repeat_jog)

    def _jog(self, axis, direction):
        if self.robot is None:
            messagebox.showwarning("Aviso", "Conecte o robô primeiro")
            return
        self._run(self._async_jog(axis, direction, float(self.entry_step.get())))

    async def _async_jog(self, axis, direction, step):
        try:
            pose = await self.robot.dashboard.get_pose()
            if not pose or len(pose) < 4:
                self._log("[ERRO] Pose invalida para JOG")
                return

            x, y, z, r = pose[0], pose[1], pose[2], pose[3]

            if axis == "x":
                x += step * direction
            elif axis == "y":
                y += step * direction
            elif axis == "z":
                z += step * direction
            elif axis == "r":
                r += step * direction

            await self.robot.motion.movj(x, y, z, r)
            self._log(f"JOG {axis.upper()} {direction:+}: ({x:.1f}, {y:.1f}, {z:.1f}, r={r:.1f})")
        except Exception as e:
            self._log(f"[ERRO] JOG: {e}")

    def _read_pose(self):
        self._run(self._async_read_pose())

    async def _async_read_pose(self):
        try:
            pose = await self.robot.dashboard.get_pose()
            pose_str = str(pose)
            self.root.after(0, lambda ps=pose_str: self.lbl_pose.config(text=f"Pose: {ps}"))
            self.root.after(0, lambda ps=pose_str: self._log(f"Pose: {ps}"))
        except Exception as e:
            self.root.after(0, lambda err=e: self._log(f"[ERRO] Ler Pose: {err}"))

    def _save_point(self):
        self._run(self._async_save_point())

    async def _async_save_point(self):
        try:
            pose = await self.robot.dashboard.get_pose()
            self.saved_points.append(pose)
            self.root.after(0, lambda: self.list_points.insert("end", str(pose)))
            self.root.after(0, lambda: self._log(f"Salvo: {pose}"))
        except Exception as e:
            self.root.after(0, lambda: self._log(f"[ERRO] {e}"))

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

    def _pick_and_place(self):
        if len(self.saved_points) < 2:
            messagebox.showwarning("Aviso", "Salve pelo menos 2 coordenadas:\n1ª = pegar | 2ª = entregar")
            return
        self._run(self._async_pick_and_place())

    async def _async_pick_and_place(self):
        try:
            pick = self.saved_points[0]
            place = self.saved_points[1]

            px, py, pz = float(pick[0]), float(pick[1]), float(pick[2])
            qx, qy, qz = float(place[0]), float(place[1]), float(place[2])

            self._log(f"Pegar em: ({px:.1f}, {py:.1f}, {pz:.1f})")
            await self.robot.motion.movj(px, py, pz, 0)
            await asyncio.sleep(0.5)

            self._log("Ligando sucção...")
            await self.robot.tool.suction(True)
            await asyncio.sleep(0.5)

            self._log(f"Entregar em: ({qx:.1f}, {qy:.1f}, {qz:.1f})")
            await self.robot.motion.movj(qx, qy, qz, 0)
            await asyncio.sleep(0.5)

            self._log("Desligando sucção...")
            await self.robot.tool.suction(False)

            self._log("Pick and place finalizado")
        except Exception as e:
            self._log(f"[ERRO] Pick and place: {e}")

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
        self._process_ui_queue()
        self.root.mainloop()

    def _process_ui_queue(self):
        try:
            action = self._ui_queue.get_nowait()
            action()
        except queue.Empty:
            pass
        self.root.after(50, self._process_ui_queue)


def main():
    app = DobotInterface()
    app.run()


if __name__ == "__main__":
    main()
