class Feed:
    def __init__(self, t_const=None, substrate_limit=None, t_fedbatch_start=None):
        self.t_const = t_const
        self.substrate_limit = substrate_limit
        self.t_fedbatch_start = t_fedbatch_start

        self.ts = None
        self.X_fedbatch_start = None
        self.feeding_started = False  # NEW: Prevents oscillation

        self.batch = True
        self.feeding_const = False
        self.feeding_exp = False
        self.feeding_first = False

    def get(self, t, S, X):
        # Reset all flags
        self.batch = False
        self.feeding_first = False
        self.feeding_exp = False
        self.feeding_const = False

        # Priority 1: Constant feeding
        if self.t_const is not None and t >= self.t_const:
            self.feeding_const = True
            return

        # Priority 2: Check feeding conditions with hysteresis
        feeding_should_start = False

        if self.t_fedbatch_start is not None and t >= self.t_fedbatch_start:
            feeding_should_start = True
            if not self.feeding_started:
                self.feeding_started = True  # Lock feeding ON
                print("Feeding started via time")

        if self.substrate_limit is not None:
            if not self.feeding_started:
                # First time: check condition
                if S <= (self.substrate_limit + 1e-6):
                    feeding_should_start = True
                    self.feeding_started = True  # Lock feeding ON
                    print("Feeding started via substrate limit")
                else:
                    pass
            else:
                # Once started, keep feeding (prevents oscillation)
                feeding_should_start = True

        # Priority 3: Set appropriate flag
        if feeding_should_start:
            if self.ts is None:
                self.ts = t
                self.X_fedbatch_start = X
                self.feeding_first = True
                print(f"Feeding started at time: {self.ts:.3f}")
                print(f"Feeding started at Biomass: {self.X_fedbatch_start:.6f}")
            else:
                self.feeding_exp = True
        else:
            self.batch = True

    def get_pulse(self, x, pulse_amount, pulse_index):
        """
        Apply a pulse addition of substrate if the current time matches a pulse time.

        Parameters:
            time 
            pulse_index (float): what do you want to increase
            pulse_amount : how much increase
            x (list): Current state vector example: [X, S, A, V, DOTa, DOT]

        Returns:
            Updated state vector with substrate added if pulse is triggered.
        """
        
            
        # Apply  pulse to specific index 
        x[-1, pulse_index] += pulse_amount
        return x
