from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd 
from matplotlib.ticker import MultipleLocator, FuncFormatter
from matplotlib.cm import get_cmap
from matplotlib.colors import to_hex, ListedColormap, BoundaryNorm
from matplotlib.patches import Patch


class MovementVisualizer:
    def __init__(self, input_dir="data", output_dir="analysis"):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.load_data()
        self.hour_ticks = list(range(0, 96, 4))
        self.hour_labels = [f"{(h % 12) or 12} {'AM' if h < 12 else 'PM'}" for h in range(24)]

    def load_data(self):
        self.residents_df = pd.read_csv(self.input_dir / "ng_residents.csv")
        self.places_df = pd.read_csv(self.input_dir / "ng_places.csv")
        self.schedules_df = pd.read_csv(self.input_dir / "ng_schedules.csv")
        self.movement_df = pd.read_csv(Path("output") / "counts_by_place_5.csv")
        self.merged_movement = self.movement_df.merge(self.places_df, on="place_id")

    def format_time(self, x, pos):
        return f"{int(x) // 60:02d}:{int(x) % 60:02d}"

    def plot_occupancy(self, place_type):
        df = self.merged_movement[self.merged_movement["type"] == place_type]
        
        if df["name"].nunique() > 1:
            raise ValueError("This version of plot_occupancy expects only one room.")

        plt.figure(figsize=(10, 5))
        room_name = df["name"].unique()[0]
        
        # Simple bar plot: x = tick, y = person_count
        plt.bar(df["tick"], df["person_count"], width=1, align="edge", color="tab:blue")

        plt.xticks(self.hour_ticks, self.hour_labels, rotation=45)
        plt.xlim(0, 96)
        plt.xlabel("Time of Day")
        plt.ylabel("Number of People")
        plt.title(f"{room_name.title()} Occupancy – First Day Only")
        plt.grid(True, axis="y")
        plt.tight_layout()
        plt.savefig(self.output_dir / f"{place_type}_occupancy.png")
        plt.close()


    def plot_gantt_for_persons(self, person_ids):
        person_colors = {pid: to_hex(get_cmap("tab10")(i)) for i, pid in enumerate(person_ids)}
        place_rows = []

        for pid in person_ids:
            row = self.residents_df[self.residents_df["person_id"] == pid].iloc[0]
            schedule_id = row["schedule_id"]
            sched = self.schedules_df[self.schedules_df["schedule_id"] == schedule_id].copy()
            sched["place_id"] = sched["place_type"].apply(lambda pt: row[pt])
            sched = sched.merge(self.places_df, on="place_id").sort_values("start")
            sched["duration"] = sched["start"].shift(-1) - sched["start"]
            sched.loc[sched.index[-1], "duration"] = 1440 - sched["start"].iloc[-1]

            for _, r in sched.iterrows():
                place_rows.append({
                    "person_id": pid,
                    "place_label": r["name"],
                    "start": r["start"],
                    "duration": r["duration"]
                })

        df = pd.DataFrame(place_rows)
        unique_places = sorted(df["place_label"].unique(), key=lambda x: ("cell" not in x, x))
        place_to_y = {place: i for i, place in enumerate(unique_places)}

        row_offsets = {}
        plt.figure(figsize=(12, 6))
        for _, row in df.iterrows():
            y_base = place_to_y[row["place_label"]]
            key = (row["place_label"], row["start"])
            offset = row_offsets.get(key, 0)
            row_offsets[key] = offset + 1
            y = y_base + (offset - 1) * 0.2

            label = f"Person {row['person_id']}"
            if label not in plt.gca().get_legend_handles_labels()[1]:
                plt.broken_barh(
                    [(row["start"], row["duration"])],
                    (y - 0.15, 0.3),
                    facecolors=person_colors[row["person_id"]],
                    edgecolors="black",
                    alpha=0.7,
                    label=label
                )
            else:
                plt.broken_barh(
                    [(row["start"], row["duration"])],
                    (y - 0.15, 0.3),
                    facecolors=person_colors[row["person_id"]],
                    edgecolors="black",
                    alpha=0.7
                )

        plt.yticks(range(len(unique_places)), unique_places)
        plt.gca().xaxis.set_major_locator(MultipleLocator(120))
        plt.gca().xaxis.set_major_formatter(FuncFormatter(self.format_time))
        plt.xticks(rotation=45)
        plt.xlim(0, 1440)
        plt.xlabel("Time (HH:MM)")
        plt.ylabel("Location")
        title = "Movement Schedule"
        if len(person_ids) == 1:
            title += f" for Person {person_ids[0]}"
        else:
            title += " – Multiple Persons"
        plt.title(title)
        plt.grid(True, axis="x")
        plt.legend(title="Person", bbox_to_anchor=(1.01, 1), loc="upper left")
        plt.tight_layout()

        filename = (
            f"person_{person_ids[0]}_gantt.png"
            if len(person_ids) == 1
            else "multi_person_gantt.png"
        )
        plt.savefig(self.output_dir / filename, dpi=300)
        plt.close()

    def plot_movement_heatmap(self, person_ids, bin_minutes=15):
        """
        Heatmap of where each person is over the day.
        Rows = people, columns = time bins, color = place.
        """
        # Build the same per-person schedule as in plot_gantt_for_persons
        place_rows = []
        for pid in person_ids:
            row = self.residents_df[self.residents_df["person_id"] == pid].iloc[0]
            schedule_id = row["schedule_id"]
            sched = self.schedules_df[self.schedules_df["schedule_id"] == schedule_id].copy()
            sched["place_id"] = sched["place_type"].apply(lambda pt: row[pt])
            sched = sched.merge(self.places_df, on="place_id").sort_values("start")
            sched["duration"] = sched["start"].shift(-1) - sched["start"]
            sched.loc[sched.index[-1], "duration"] = 1440 - sched["start"].iloc[-1]

            for _, r in sched.iterrows():
                place_rows.append({
                    "person_id": pid,
                    "place_label": r["name"],
                    "start": r["start"],
                    "duration": r["duration"]
                })

        df = pd.DataFrame(place_rows)

        # Order persons and places in a stable way
        person_ids = list(person_ids)
        person_to_row = {pid: i for i, pid in enumerate(person_ids)}

        unique_places = sorted(df["place_label"].unique(), key=lambda x: ("cell" not in x, x))
        place_to_idx = {place: i for i, place in enumerate(unique_places)}

        # Time discretization
        n_bins = 1440 // bin_minutes
        mat = np.full((len(person_ids), n_bins), fill_value=-1, dtype=int)

        for _, r in df.iterrows():
            pid = r["person_id"]
            if pid not in person_to_row:
                continue
            row_idx = person_to_row[pid]
            place_idx = place_to_idx[r["place_label"]]

            start_min = int(r["start"])
            end_min = int(r["start"] + r["duration"])
            start_bin = start_min // bin_minutes
            end_bin = min(n_bins, (end_min + bin_minutes - 1) // bin_minutes)

            if start_bin < end_bin:
                mat[row_idx, start_bin:end_bin] = place_idx

        # Mask "no data" entries
        mat_masked = np.ma.masked_where(mat < 0, mat)

        # Categorical colormap for places
        colors = [get_cmap("tab20")(i % 20) for i in range(len(unique_places))]
        cmap = ListedColormap(colors)
        bounds = np.arange(len(unique_places) + 1) - 0.5
        norm = BoundaryNorm(bounds, cmap.N)

        fig, ax = plt.subplots(figsize=(12, max(4, len(person_ids) * 0.25)))
        im = ax.imshow(mat_masked, aspect="auto", cmap=cmap, norm=norm)

        # Y axis: people
        ax.set_yticks(range(len(person_ids)))
        ax.set_yticklabels([f"P{pid}" for pid in person_ids])

        # X axis: time of day in hours
        bins_per_hour = 60 // bin_minutes
        x_ticks = np.arange(0, n_bins + 1, bins_per_hour * 2)  # every 2 hours
        x_labels = []
        for b in x_ticks:
            minutes = b * bin_minutes
            hour = minutes // 60
            x_labels.append(f"{hour:02d}:00")
        ax.set_xticks(x_ticks)
        ax.set_xticklabels(x_labels, rotation=45, ha="right")

        ax.set_xlabel("Time of Day")
        ax.set_ylabel("Person")

        ax.set_title("Daily Movement Heatmap")

        # Legend for places
        legend_handles = [Patch(color=colors[i], label=unique_places[i]) for i in range(len(unique_places))]
        ax.legend(handles=legend_handles, title="Location", bbox_to_anchor=(1.01, 1), loc="upper left")

        plt.tight_layout()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        plt.savefig(self.output_dir / "movement_heatmap.png", dpi=300)
        plt.close()


if __name__ == "__main__":
    viz = MovementVisualizer()

    # Occupancy plots
    viz.plot_occupancy("gym")
    viz.plot_occupancy("cafeteria")
    viz.plot_occupancy("yard")

    # Gantt chart: single person
    viz.plot_gantt_for_persons([5])

    # Gantt chart: multiple people
    viz.plot_gantt_for_persons([5, 7])

    sample_ids = viz.residents_df["person_id"].head(30).tolist()
    viz.plot_movement_heatmap(sample_ids, bin_minutes=15)
