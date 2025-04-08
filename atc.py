import tkinter as tk
from tkinter import ttk, messagebox
import networkx as nx
import pandas as pd
import random
from PIL import Image, ImageTk, ImageEnhance

# --- Load Graph ---
def build_air_route_graph(airports_file, routes_file):
    G = nx.DiGraph()
    airports = pd.read_csv(airports_file)
    routes = pd.read_csv(routes_file)

    for _, row in airports.iterrows():
        G.add_node(int(row['id']), name=row['name'], pos=(row['lat'], row['lon']))

    for _, row in routes.iterrows():
        G.add_edge(
            int(row['from']), int(row['to']),
            weight=row['distance_km'],
            duration=row['avg_duration_min'],
            fuel=row['fuel_cost_l'],
            congestion=row['congestion_factor']
        )
    return G, airports

# --- Multi-Objective Optimizer ---
def dijkstra_multi_objective(graph, start, end, weights):
    try:
        paths = list(nx.all_simple_paths(graph, start, end))
    except nx.NetworkXNoPath:
        return None, float('inf')

    best_score = float('inf')
    best_path = None

    for path in paths:
        total = {'distance': 0, 'duration': 0, 'fuel': 0, 'congestion': 0}
        for i in range(len(path) - 1):
            edge = graph[path[i]][path[i + 1]]
            total['distance'] += edge['weight']
            total['duration'] += edge['duration']
            total['fuel'] += edge['fuel']
            total['congestion'] += edge['congestion']

        score = (weights['distance'] * total['distance'] +
                 weights['duration'] * total['duration'] +
                 weights['fuel'] * total['fuel'] +
                 weights['congestion'] * total['congestion'])

        if score < best_score:
            best_score = score
            best_path = path

    return best_path, best_score

# --- Weather Simulation ---
def simulate_weather_conditions(route_graph):
    for u, v, data in route_graph.edges(data=True):
        weather_delay = random.uniform(0, 20)
        data['duration'] += weather_delay
        data['congestion'] += random.uniform(0, 0.2)

# --- Performance Analysis ---
def analyze_path(graph, path):
    distance = duration = fuel = congestion = 0
    for i in range(len(path) - 1):
        edge = graph[path[i]][path[i + 1]]
        distance += edge['weight']
        duration += edge['duration']
        fuel += edge['fuel']
        congestion += edge['congestion']
    return {
        'total_distance_km': distance,
        'flight_duration_min': duration,
        'fuel_consumed_l': fuel,
        'avg_congestion': congestion / (len(path) - 1)
    }

# --- GUI ---
class AirTrafficGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("✈️ Flight Route Planner")
        self.root.geometry("1000x750")

        # Load background image
        self.original_bg_image = Image.open("C:/Users/PRIYAM/OneDrive/Desktop/Flight Route Planner/plane.jpg")
        self.bg_label = tk.Label(self.root)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        self.update_background()
        self.root.bind("<Configure>", self.on_resize)

        # Set style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TLabel", font=('Segoe UI', 10))
        style.configure("TButton", font=('Segoe UI', 10, 'bold'), background="#1f6aa5", foreground="white")
        style.configure("TCombobox", font=('Segoe UI', 10))
        style.configure("TEntry", font=('Segoe UI', 10))

        self.graph, self.airports_df = build_air_route_graph(
            "C:/Users/PRIYAM/OneDrive/Desktop/Flight Route Planner/airports.csv",
            "C:/Users/PRIYAM/OneDrive/Desktop/Flight Route Planner/routes.csv"
        )
        simulate_weather_conditions(self.graph)

        self.main_frame = tk.Frame(self.root, bg='#ffffff', bd=3, relief='ridge')
        self.main_frame.place(relx=0.5, rely=0.5, anchor='center')

        self.setup_widgets()

    def update_background(self):
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        if width > 1 and height > 1:
            resized = self.original_bg_image.resize((width, height), Image.LANCZOS)
            enhancer = ImageEnhance.Brightness(resized)
            dimmed_image = enhancer.enhance(0.4)
            self.bg_photo = ImageTk.PhotoImage(dimmed_image)
            self.bg_label.config(image=self.bg_photo)

    def on_resize(self, event):
        self.update_background()

    def setup_widgets(self):
        ttk.Label(self.main_frame, text="🌍 Flight Route Planner", font=('Segoe UI', 16, 'bold')).grid(row=0, column=0, columnspan=2, pady=10)

        ttk.Label(self.main_frame, text="Select Source Airport").grid(row=1, column=0, padx=10, pady=5, sticky='e')
        self.source_combo = ttk.Combobox(self.main_frame, values=self.airports_df['name'].tolist(), width=35)
        self.source_combo.grid(row=1, column=1, padx=10, pady=5)

        ttk.Label(self.main_frame, text="Select Destination Airport").grid(row=2, column=0, padx=10, pady=5, sticky='e')
        self.dest_combo = ttk.Combobox(self.main_frame, values=self.airports_df['name'].tolist(), width=35)
        self.dest_combo.grid(row=2, column=1, padx=10, pady=5)

        labels = ['Distance Weight', 'Duration Weight', 'Fuel Weight', 'Congestion Weight']
        self.weight_entries = {}
        for i, label in enumerate(labels):
            ttk.Label(self.main_frame, text=label).grid(row=3+i, column=0, padx=10, pady=5, sticky='e')
            entry = ttk.Entry(self.main_frame, width=10)
            entry.grid(row=3+i, column=1, padx=10, sticky='w')
            entry.insert(0, "1.0")
            self.weight_entries[label.split()[0].lower()] = entry

        self.run_btn = ttk.Button(self.main_frame, text="🚀 Find Optimal Route", command=self.find_route)
        self.run_btn.grid(row=7, column=0, columnspan=2, pady=20)

        result_frame = tk.Frame(self.main_frame)
        result_frame.grid(row=8, column=0, columnspan=2, padx=10, pady=10)
        self.result_text = tk.Text(result_frame, height=10, width=75, state='disabled', wrap="word", bg="#f2f4f6", font=('Segoe UI', 10))
        scroll = ttk.Scrollbar(result_frame, command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=scroll.set)
        self.result_text.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def find_route(self):
        try:
            src_name = self.source_combo.get()
            dest_name = self.dest_combo.get()

            if not src_name or not dest_name:
                raise ValueError("Both source and destination airports must be selected.")

            src_id = int(self.airports_df[self.airports_df['name'] == src_name]['id'].values[0])
            dest_id = int(self.airports_df[self.airports_df['name'] == dest_name]['id'].values[0])
            weights = {key: float(entry.get()) for key, entry in self.weight_entries.items()}
            path, score = dijkstra_multi_objective(self.graph, src_id, dest_id, weights)

            self.result_text.config(state='normal')
            self.result_text.delete("1.0", tk.END)

            if path:
                route_names = [self.graph.nodes[n]['name'] for n in path]
                metrics = analyze_path(self.graph, path)

                self.result_text.insert(tk.END, f"🛫 Best Route:\n{' → '.join(route_names)}\n\n")
                self.result_text.insert(tk.END, "📊 Performance Metrics:\n")
                for k, v in metrics.items():
                    self.result_text.insert(tk.END, f"{k.replace('_', ' ').title()}: {round(v, 2)}\n")
            else:
                self.result_text.insert(tk.END, "⚠️ No optimal route found.")

            self.result_text.config(state='disabled')
        except Exception as e:
            messagebox.showerror("Error", str(e))


# --- Main ---
if __name__ == "__main__":
    root = tk.Tk()
    app = AirTrafficGUI(root)
    root.mainloop()
