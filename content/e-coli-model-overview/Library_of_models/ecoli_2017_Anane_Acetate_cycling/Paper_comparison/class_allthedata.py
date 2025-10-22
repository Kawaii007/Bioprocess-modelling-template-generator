import numpy as np
import datetime
import os

class AllthedataBuilder:
    def __init__(self, variables: dict, inputs: dict, rates: dict, x: np.ndarray, t: np.ndarray, t_fedbatch = None, t_constant_feed = None, description = "Simulation"):
        self.variables = variables
        self.inputs = inputs
        self.rates = rates
        self.x = x
        self.t = t
        self.description = description

        # Time settings (could be generalized)
        self.t0 = float(t[0])
        self.t_end = float(t[-1])
        self.t_fedbatch = t_fedbatch
        self.t_constant_feed = t_constant_feed

        # Placeholders for data, set in build()
        self.data = None
        self.t_data = None

    def init_saving(self, run_description="", run_id="run", path_save="", path_to_results_load=None):
        """
        Function to initialize saving (e.g. create folder if not existing.).

        :param run_description: Optional description string for naming the folder
        :param run_id: Run identifier (int or str)
        :param path_save: Base path to save results, defaults to current working dir
        :param path_to_results_load: If provided, load results from here instead of creating a new folder
        :return: (path_to_results, datestring)
        """
        datestring = datetime.datetime.now().strftime("%Y%m%d_%H-%M-%S")

        # Decide identifier
        if run_description:
            identifier = run_description
        else:
            identifier = str(run_id)

        # Base folder to save results
        path_to_results_folder = os.getcwd() if path_save == "" else os.path.join(path_save)

        if not os.path.exists(path_to_results_folder):
            os.makedirs(path_to_results_folder, exist_ok=True)

        # Decide final save path
        if path_to_results_load:
            path_to_results = path_to_results_load
        else:
            path_to_results = f'{os.path.join(path_to_results_folder, datestring)}_{identifier}'

        print(f"Results are saved here: {path_to_results}")

        if not os.path.exists(path_to_results):
            os.makedirs(path_to_results, exist_ok=True)

        return path_to_results, datestring, run_id


    # -----------------------------
    # Core: Build method
    # -----------------------------
    def build(self, data=None, columns=None, t_data=None):
        """
        Builds the full allthedata structure.

        Parameters:
        - data: np.ndarray or dict
            Experimental or measured data
        - columns: list
            Column names corresponding to `data` order (required if ndarray)
        - t_data: np.ndarray
            Time vector for the experimental data (defaults to self.t)
        """
        # Store experimental time vector
        self.t_data = t_data if t_data is not None else self.t

        # Align data with variables
        if data is not None:
            self.data = self._align_data_with_variables(data, columns)
        else:
            self.data = None

        # Build main structured dictionary
        allthedata = {
            "description": self.description,
            "simulation_data": {
                "times": self.t,
                "vals": self._extract_state_values(),
                "sensitivities": {},
                "sensitivities (weighted)": {},
                "sensitivity_matrix": {},
            },
            "starttime": self.t0,
            "endtime": self.t_end,
            "duration": self.t_end - self.t0,
            "variables": self._build_variables_section(),
            "inputs": self._build_inputs_section(),
            "measurement_times": [],
        }
        return allthedata


    # -----------------------------
    # Helper: Align experimental data
    # -----------------------------
    def _align_data_with_variables(self, data, columns=None):
        var_names = list(self.variables.keys())
        n_vars = len(var_names)

        if isinstance(data, dict):
            aligned = np.zeros((len(self.t_data), n_vars))
            for i, name in enumerate(var_names):
                if name in data:
                    aligned[:, i] = np.array(data[name])
                else:
                    aligned[:, i] = np.nan
                    print(f"⚠️ Warning: '{name}' not found in data dict — filled with NaN.")
        elif isinstance(data, np.ndarray):
            if columns is None:
                raise ValueError("If data is ndarray, you must provide `columns`.")
            aligned = np.zeros((data.shape[0], n_vars))
            for i, name in enumerate(var_names):
                if name in columns:
                    idx = columns.index(name)
                    aligned[:, i] = data[:, idx]
                else:
                    aligned[:, i] = np.nan
                    print(f"⚠️ Warning: '{name}' not found in data columns — filled with NaN.")
        else:
            raise TypeError("Data must be a dict or numpy.ndarray.")

        print("✅ Data successfully aligned with variable order.")
        return aligned

    def _extract_state_values(self):
        vals = {}
        for idx, var in enumerate(self.variables.keys()):
            vals[var] = self.x[:, idx]

        n_states = len(self.variables)

        for id, rate in enumerate(self.rates.keys()):
            id = n_states + id
            vals[rate] = self.x[:, id]
        return vals

    def _format_description_with_unit(self, desc: str, unit: str) -> str:
        """
        Merge description and unit, converting '/' to HTML <sup>-1</sup>.
        Examples:
            [g/L] -> [g L<sup>-1</sup>]
            [g/g/h] -> [g g<sup>-1</sup> h<sup>-1</sup>]
        """
        if not unit:
            return desc

        if "/" in unit:
            # Remove brackets temporarily
            unit_body = unit.strip("[]")
            parts = unit_body.split("/")
            formatted_parts = [parts[0]]  # first part as-is
            for p in parts[1:]:
                formatted_parts.append(f"{p}<sup>-1</sup>")
            unit = "[" + " ".join(formatted_parts) + "]"

        return f"{desc} {unit}"

    def _build_variables_section(self):
        var_section = {}

        for idx, (name, meta) in enumerate(self.variables.items()):
            boundaries = meta.get("boundaries", [None, None])
            if boundaries == [None, None]:
                boundaries = [0, np.inf]

            desc = meta.get("description", name)
            unit = meta.get("unit", "")
            full_desc = self._format_description_with_unit(desc, unit)

            var_section[name] = {
                "times": self.t_data,
                "vals": [] if self.data is None else self.data[:, idx],
                "std": [],
                "initial_value": meta.get("initial_value", None),
                "boundaries": boundaries,
                "description": full_desc,
                "estimable": True if meta.get("estimable") is None else meta.get("estimable"),
                "weight": 1 if meta.get("weight") is None else meta.get("weight"),
                "if_dtw": False,
                "plotting": {
                    "plot": True if meta.get("plotting", {}).get("plot") is None else meta.get("plotting", {}).get("plot"),
                    "range": [np.inf, np.inf],
                    "range_fedbatch": True if meta.get("plotting", {}).get("range_fedbatch") is None else meta.get("plotting",{}).get("range_fedbatch"),
                    "dtick": None,
                },
                "conversion_factor": None if meta.get("conversion_factor") is None else meta.get("conversion_factor"),
                "volume_related": True if meta.get("volume_related") is None else meta.get("volume_related"),
                "ilabname": None,
            }

        n_states = len(self.variables)

        for id, (name, meta) in enumerate(self.rates.items()):
            id_total = n_states + id
            desc = meta.get("description", name)
            unit = meta.get("unit", "")
            full_desc = self._format_description_with_unit(desc, unit)

            # ✅ Safe check for data availability
            if self.data is not None and id_total < self.data.shape[1]:
                vals = self.data[:, id_total]
            else:
                vals = np.full_like(self.t_data, np.nan)
                if self.data is not None:
                    print(f"⚠️ Warning: '{name}' (rate) not found in data — filled with NaN.")

            var_section[name] = {
                "times": self.t_data,
                "vals": vals,
                "std": [],
                "initial_value": meta.get("initial_value"),
                "boundaries": [np.inf, np.inf],
                "description": full_desc,
                "estimable": True,
                "weight": 1,
                "if_dtw": False,
                "plotting": {
                    "plot": True,
                    "range": [np.inf, np.inf],
                    "range_fedbatch": True,
                    "dtick": None,
                },
                "conversion_factor": None,
                "volume_related": True,
                "ilabname": None,
            }
        return var_section
    def _build_inputs_section(self):
        inputs_section = {}
        if self.t_constant_feed is not None and "Induction" not in self.inputs:
            inputs_section["Constant Feed"] = {
                    "times": self.t_constant_feed,
                    "vals": self.x[:,0],  # placeholder profile
                    "type": None,
                    "description": 'Constant Feed',
                    "initial_value": None,
                    "plotting": {
                        "plot": False,
                        "range": [0, 1],
                        "range_fedbatch": True,
                        "stem": True,
                    },
                    "ilabname": None,
                }
        for name, meta in self.inputs.items():
            if name == "Feed" and self.t_fedbatch is not None:
                inputs_section[name] = {
                    "times": self.t_fedbatch,
                    "vals": self.x[:,0],  # placeholder profile
                    "type": None,
                    "description": meta.get("description", name),
                    "initial_value": None,
                    "plotting": {
                        "plot": False,
                        "range": [0, 1],
                        "range_fedbatch": True,
                        "stem": True,
                    },
                    "ilabname": None,
                }
            elif name == "Induction" and self.t_constant_feed is not None:
                inputs_section[name] = {
                    "times": self.t_constant_feed,
                    "vals": np.zeros_like(self.t_constant_feed),  # placeholder profile
                    "type": None,
                    "description": meta.get("description", name),
                    "initial_value": None,
                    "plotting": {
                        "plot": False,
                        "range": [0, 1],
                        "range_fedbatch": True,
                        "stem": True,
                    },
                    "ilabname": None,
                }
            elif name != "Feed":
                inputs_section[name] = {
                    "times": self.t,  # could be replaced by specific feed times
                    "vals": np.zeros_like(self.t),  # placeholder profile
                    "type": None,
                    "description": meta.get("description", name),
                    "initial_value": None,
                    "plotting": {
                        "plot": False,
                        "range": [0, 1],
                        "range_fedbatch": True,
                        "stem": True,
                    },
                    "ilabname": None,
                }

        return inputs_section
