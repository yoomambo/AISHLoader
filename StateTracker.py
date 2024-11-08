
class StateTracker:
    def __init__(self):
        self.state_history = []

    def get_state(self):
        if len(self.state_history) == 0:
            return None
        return self.state_history[-1]
    
    def _track_state(self, state):
        self.state_history.append(state)

        #Limit history to 100 states
        if len(self.state_history) > 100:
            self.state_history.pop(0)