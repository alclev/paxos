import tkinter as tk
import random
import math
import time
import threading

class PaxosGUI:
    def __init__(self, root, nodes):
        self.root = root
        self.nodes = nodes
        self.width = 1000
        self.height = 800
        self.canvas = tk.Canvas(self.root, width=self.width, height=self.height, bg="white")
        self.canvas.pack()

        self.phase_label = tk.Label(self.root, text="Phase: None", font=("Arial", 14))
        self.phase_label.pack()

        self.message_box = tk.Text(self.root, height=15, width=120, font=("Arial", 10))
        self.message_box.pack()

        self.button_frame = tk.Frame(self.root)
        self.button_frame.pack(pady=5)

        self.propose_button = tk.Button(self.button_frame, text="Propose Value (Random Leader)",
                                         command=self.propose_random, font=("Arial", 10))
        self.propose_button.grid(row=0, column=0, padx=5)

        self.crash_button = tk.Button(self.button_frame, text="Crash Random Node",
                                      command=self.crash_random, font=("Arial", 10))
        self.crash_button.grid(row=0, column=1, padx=5)

        self.recover_button = tk.Button(self.button_frame, text="Recover All",
                                        command=self.recover_all, font=("Arial", 10))
        self.recover_button.grid(row=0, column=2, padx=5)

        self.step_button = tk.Button(self.button_frame, text="Step",
                                     command=self.step_phase, font=("Arial", 10))
        self.step_button.grid(row=0, column=3, padx=5)

        self.run_button = tk.Button(self.button_frame, text="Run",
                                    command=self.run_full, font=("Arial", 10))
        self.run_button.grid(row=0, column=4, padx=5)

        self.node_positions = {}
        self.inflight_messages = []
        self.current_phase = None
        self.current_leader = None
        self.running = False
        self.phases = []  # Will hold tuples of (phase_name, phase_function)
        self.current_phase_index = 0
        self.auto_run_thread = None

        self.layout_nodes()
        self.legend()
        self.refresh()

    def layout_nodes(self):
        r = 300
        cx, cy = self.width/2, self.height/2 - 50
        angle_step = 2*math.pi/len(self.nodes)
        for i, n in enumerate(self.nodes):
            angle = i*angle_step
            x = cx + r*math.cos(angle)
            y = cy + r*math.sin(angle)
            self.node_positions[n.id] = (x,y)

    def legend(self):
        self.message_box.insert(tk.END, "LEGEND:\n")
        self.message_box.insert(tk.END, " Blue lines: PREPARE / PROMISE messages\n")
        self.message_box.insert(tk.END, " Green lines: ACCEPT / ACCEPTED messages\n")
        self.message_box.insert(tk.END, " Red lines: COMMIT messages\n\n")
        self.message_box.insert(tk.END, "CONTROLS:\n")
        self.message_box.insert(tk.END, " 'Propose Value' chooses a leader and sets up phases.\n")
        self.message_box.insert(tk.END, " 'Step' moves to the next Paxos phase (Prepare -> Accept -> Commit).\n")
        self.message_box.insert(tk.END, " 'Run' automatically runs through all phases.\n")
        self.message_box.insert(tk.END, " 'Crash Random Node' and 'Recover All' simulate failures.\n\n")

    def draw_nodes(self):
        self.canvas.delete("all")

        # Draw fully connected lines in background
        for i, n1 in enumerate(self.nodes):
            for j, n2 in enumerate(self.nodes):
                if i < j:
                    x1, y1 = self.node_positions[n1.id]
                    x2, y2 = self.node_positions[n2.id]
                    self.canvas.create_line(x1, y1, x2, y2, fill="gray", dash=(2,2))

        # Draw nodes
        for n in self.nodes:
            x, y = self.node_positions[n.id]
            color = "red" if n.crashed else "lightgreen"
            outline = "black"
            width = 2
            if n.is_leader:
                outline = "blue"
                width = 3
            self.canvas.create_oval(x-30, y-30, x+30, y+30, fill=color, outline=outline, width=width)
            text = f"N{n.id}"
            if n.is_leader:
                text += "(L)"
            self.canvas.create_text(x, y, text=text, font=("Arial", 12, "bold"))

            # Show node state beneath node
            state_text = []
            if n.acceptor.promised_ballot is not None:
                state_text.append(f"Promised: b={n.acceptor.promised_ballot}")
            if n.acceptor.accepted_ballot is not None:
                state_text.append(f"Accepted: b={n.acceptor.accepted_ballot}, v={n.acceptor.accepted_value}")
            if n.learner.learned_value is not None:
                state_text.append(f"Learned: {n.learner.learned_value}")
            if n.last_action:
                state_text.append(n.last_action)
            if state_text:
                self.canvas.create_text(x, y+45, text="\n".join(state_text), font=("Arial", 10), fill="blue")

    def draw_messages(self):
        current_time = time.time()
        alive_msgs = []
        for m in self.inflight_messages:
            elapsed = current_time - m["start_time"]
            if elapsed < m["duration"]:
                sx, sy = self.node_positions[m["sender"]]
                rx, ry = self.node_positions[m["receiver"]]
                t = elapsed / m["duration"]
                mx = sx + (rx - sx)*t
                my = sy + (ry - sy)*t
                color = "blue"
                if m["msg_type"] in ["ACCEPT","ACCEPTED"]:
                    color = "green"
                elif m["msg_type"] == "COMMIT":
                    color = "red"
                self.canvas.create_line(sx, sy, mx, my, arrow=tk.LAST, fill=color, width=2)
                self.canvas.create_text((sx+mx)/2, (sy+my)/2 - 10, text=m["msg_type"], fill=color, font=("Arial", 10))
                alive_msgs.append(m)
        self.inflight_messages = alive_msgs

    def update_phase(self, phase):
        self.current_phase = phase
        self.phase_label.config(text=f"Phase: {phase}")

    def log(self, msg):
        self.message_box.insert(tk.END, msg+"\n")
        self.message_box.see(tk.END)

    def crash_random(self):
        alive = [n for n in self.nodes if not n.crashed]
        if not alive:
            self.log("No alive nodes to crash.")
            return
        n = random.choice(alive)
        n.crash()
        self.log(f"Node {n.id} crashed.")

    def recover_all(self):
        for n in self.nodes:
            n.recover()
        self.log("All nodes recovered.")

    def propose_random(self):
        alive = [n for n in self.nodes if not n.crashed]
        if not alive:
            self.log("No alive nodes to propose.")
            return
        leader = random.choice(alive)
        for n in self.nodes:
            n.is_leader = False
        leader.is_leader = True
        self.current_leader = leader
        val = f"Val{random.randint(1,100)}"
        self.log(f"Node {leader.id} chosen as Leader. Proposing value: {val}")

        # Instead of doing all phases at once, set up a phase list:
        # Prepare phase (already implemented in proposer.start_proposal)
        # Accept phase (we'll call a new method in proposer)
        # Commit phase (call another method)
        self.phases = [
            ("Prepare", lambda: leader.start_proposal(val)),
            ("Accept", lambda: leader.proposer.enter_accept_phase()),
            ("Commit", lambda: leader.proposer.enter_commit_phase())
        ]
        self.current_phase_index = 0
        self.step_phase()

    def step_phase(self):
        if self.current_phase_index < len(self.phases):
            phase_name, phase_func = self.phases[self.current_phase_index]
            self.update_phase(phase_name)
            self.current_phase_index += 1
            # Execute the phase function after a short delay to visualize
            self.root.after(500, phase_func)
        else:
            self.log("All phases completed.")

    def run_full(self):
        # Run all phases automatically
        def run_phases():
            while self.current_phase_index < len(self.phases):
                time.sleep(1.5)
                self.root.event_generate("<<Step>>", when="tail")
        self.root.bind("<<Step>>", lambda e: self.step_phase())
        self.auto_run_thread = threading.Thread(target=run_phases, daemon=True)
        self.auto_run_thread.start()

    def show_message_pass(self, sender_id, receiver_id, msg_type):
        self.inflight_messages.append({
            "sender": sender_id,
            "receiver": receiver_id,
            "msg_type": msg_type,
            "start_time": time.time(),
            "duration": 1.5
        })

    def refresh(self):
        self.draw_nodes()
        self.draw_messages()
        for n in self.nodes:
            if n.learner.learned_value is not None:
                self.log(f"Node {n.id} learned value: {n.learner.learned_value}")
                n.last_action = f"Learned: {n.learner.learned_value}"
                n.learner.learned_value = None
        self.root.after(100, self.refresh)
